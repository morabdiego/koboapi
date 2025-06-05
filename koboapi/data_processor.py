"""Procesa los datos de envío de encuestas."""

from typing import Dict, List, Any, Optional
import pandas as pd
from collections import defaultdict
from .models import SurveyStructure, RepeatGroup

class DataProcessor:  # ProcesadorDatos
    """Processes survey submissions into structured DataFrames."""
    """Procesa los envíos de encuestas en DataFrames estructurados."""

    # Lista de columnas de metadatos que siempre están presentes en los envíos de KoBoToolbox
    METADATA_COLUMNS = [  # COLUMNAS_METADATOS
        '_id', '__version__',
        '_xform_id_string', '_uuid', '_attachments',
        '_status', '_geolocation', '_submission_time', '_tags',
        '_notes', '_validation_status', '_submitted_by'
    ]

    def __init__(self, structure: SurveyStructure):  # estructura
        """
        Initializes the processor with the survey structure.
        Inicializa el procesador con la estructura de la encuesta.

        Args:
            structure: Object containing the complete survey structure
            estructura: Objeto que contiene la estructura completa de la encuesta
        """
        self.structure = structure  # self.estructura

    def process_submissions(self, submissions: List[Dict[str, Any]]) -> List[pd.DataFrame]:  # procesar_envios, envios
        """
        Main method that processes all submissions and converts them to DataFrames.
        Método principal que procesa todos los envíos y los convierte en DataFrames.

        Args:
            submissions: List of dictionaries with each submission's data
            envios: Lista de diccionarios con los datos de cada envío

        Returns:
            List of DataFrames: [main_DataFrame, group1_DataFrame, group2_DataFrame, ...]
            Lista de DataFrames: [DataFrame_principal, DataFrame_grupo1, DataFrame_grupo2, ...]
        """
        # Si no hay envíos, retornar lista vacía
        if not submissions:
            return []

        # Lista que contendrá todos los DataFrames resultantes
        dataframes = []

        # PASO 1: Crear DataFrame principal con preguntas que no se repiten
        main_df = self._create_main_dataframe(submissions)  # df_principal, _crear_dataframe_principal
        # Solo agregar si tiene datos
        if not main_df.empty:
            dataframes.append(main_df)

        # PASO 2: Crear DataFrames para cada grupo repetido
        # Obtener grupos ordenados por nivel de anidamiento (0, 1, 2, etc.)
        sorted_groups = self._get_sorted_repeat_groups()  # grupos_ordenados, _obtener_grupos_repetidos_ordenados

        # Procesar cada grupo repetido
        for group_name, group in sorted_groups:  # nombre_grupo, grupo
            # Crear DataFrame específico para este grupo
            group_df = self._create_repeat_dataframe(submissions, group)  # df_grupo, _crear_dataframe_repetido
            # Solo agregar si tiene datos
            if not group_df.empty:
                dataframes.append(group_df)

        return dataframes

    def _create_main_dataframe(self, submissions: List[Dict[str, Any]]) -> pd.DataFrame:  # _crear_dataframe_principal, envios
        """
        Creates the main DataFrame with questions that are NOT in repeat groups.
        Crea el DataFrame principal con preguntas que NO están en grupos repetidos.

        Args:
            submissions: Complete list of submissions
            envios: Lista completa de envíos

        Returns:
            DataFrame with one row per submission and columns for main questions
            DataFrame con una fila por envío y columnas para preguntas principales
        """
        # Obtener solo las preguntas que están en el nivel raíz (path vacío)
        main_questions = self.structure.get_questions_by_path("")  # preguntas_principales

        # Lista para almacenar todas las filas del DataFrame
        all_rows = []  # todas_filas

        # Procesar cada envío individual
        for submission in submissions:  # envio
            # Crear fila vacía con todas las columnas necesarias
            row = self._initialize_row(main_questions)  # fila, _inicializar_fila

            # Llenar la fila con los datos del envío actual
            self._fill_row_data(row, submission, is_main=True)  # _llenar_datos_fila, es_principal

            # Agregar fila completa a la lista
            all_rows.append(row)

        # Convertir lista de filas en DataFrame
        return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()

    def _create_repeat_dataframe(self, submissions: List[Dict[str, Any]], group: RepeatGroup) -> pd.DataFrame:  # _crear_dataframe_repetido, envios, grupo
        """
        Creates DataFrame for a specific repeat group.
        Crea DataFrame para un grupo repetido específico.

        Args:
            submissions: Complete list of submissions
            envios: Lista completa de envíos
            group: RepeatGroup object with group information to process
            grupo: Objeto RepeatGroup con información del grupo a procesar

        Returns:
            DataFrame with multiple rows per submission (one per repetition)
            DataFrame con múltiples filas por envío (una por cada repetición)
        """
        # Filtrar preguntas que pertenecen a este grupo específico
        group_questions = {  # preguntas_grupo
            name: q for name, q in self.structure.questions.items()  # nombre
            # Incluir preguntas cuyo path coincide exactamente o empieza con el nombre del grupo
            if q.path == group.name or q.path.startswith(f"{group.name}/")
        }

        # Lista para almacenar todas las filas de todas las repeticiones
        all_rows = []  # todas_filas

        # Procesar cada envío
        for submission in submissions:  # envio
            # Obtener ID único del envío para referencias
            submission_id = submission.get('_id', submission.get('meta/instanceID', ''))  # id_envio

            # Extraer todas las repeticiones de este grupo para este envío
            group_rows = self._extract_repeat_data(submission, group, group_questions, submission_id)  # filas_grupo, _extraer_datos_repetidos

            # Agregar todas las filas de este envío a la lista total
            all_rows.extend(group_rows)

        # Convertir todas las filas en DataFrame
        return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()

    def _initialize_row(self, questions: Dict[str, Any]) -> Dict[str, Any]:  # _inicializar_fila, preguntas
        """
        Creates an empty row with all necessary columns initialized to None.
        Crea una fila vacía con todas las columnas necesarias inicializadas en None.

        Args:
            questions: Dictionary of relevant questions for this row
            preguntas: Diccionario de preguntas relevantes para esta fila

        Returns:
            Dictionary with all columns initialized to None
            Diccionario con todas las columnas inicializadas en None
        """
        row = {}  # fila

        # Agregar columnas de metadatos del sistema
        for col in self.METADATA_COLUMNS:
            row[col] = None

        # Agregar columnas para cada pregunta
        for question in questions.values():  # pregunta
            # Usar el nombre original de la pregunta como nombre de columna
            row[question.original_name] = None

        return row

    def _fill_row_data(self, row: Dict[str, Any], data: Dict[str, Any], is_main: bool = False) -> None:  # _llenar_datos_fila, fila, datos, es_principal
        """
        Fills a row with actual submission data.
        Llena una fila con datos reales del envío.

        Args:
            row: Row dictionary to fill (modified in place)
            fila: Diccionario de fila a llenar (se modifica en el lugar)
            data: Submission or repetition data
            datos: Datos del envío o repetición
            is_main: If True, we're processing the main level
            es_principal: Si es True, estamos procesando el nivel principal
        """
        # Iterar sobre cada campo de datos
        for key, value in data.items():  # clave, valor
            # Omitir campos que son listas (datos repetidos)
            if not isinstance(value, list):
                # Extraer el nombre de la columna (quitar prefijos de ruta)
                original_key = key.split('/')[-1] if '/' in key else key  # clave_original

                # Solo asignar si la columna existe en la fila
                if original_key in row:
                    row[original_key] = value

    def _extract_repeat_data(self, submission: Dict[str, Any], group: RepeatGroup, questions: Dict[str, Any], submission_id: str) -> List[Dict[str, Any]]:  # _extraer_datos_repetidos, envio, grupo, preguntas, id_envio
        """
        Extracts data from a repeat group, handling nesting.
        Extrae datos de un grupo repetido, manejando anidamiento.

        Args:
            submission: Complete submission data
            envio: Datos completos del envío
            group: Repeat group information
            grupo: Información del grupo repetido
            questions: Questions belonging to this group
            preguntas: Preguntas que pertenecen a este grupo
            submission_id: Unique ID of parent submission
            id_envio: ID único del envío padre

        Returns:
            List of rows (one per group repetition)
            Lista de filas (una por cada repetición del grupo)
        """
        # Dividir el nombre del grupo en partes para manejar anidamiento
        # Ejemplo: "grupo1/grupo2" -> ["grupo1", "grupo2"]
        path_parts = group.name.split('/')  # partes_ruta
        rows = []  # filas

        # Verificar el nivel de anidamiento del grupo
        if group.level == 0:
            # CASO 1: Grupo de primer nivel (no anidado)
            # Buscar directamente en el envío usando el nombre simple del grupo
            items = submission.get(group.simple_name, [])  # elementos

            # Procesar cada elemento repetido
            for item in items:  # elemento
                # Crear nueva fila con referencia al envío padre
                row = {'_parent_id': submission_id}  # fila

                # Inicializar fila con columnas del grupo
                self._initialize_row_for_group(row, questions)  # _inicializar_fila_para_grupo

                # Llenar fila con datos del elemento
                self._fill_row_data(row, item)

                # Agregar fila a la lista
                rows.append(row)
        else:
            # CASO 2: Grupo anidado (dentro de otro grupo repetido)
            # Usar método recursivo para navegar la estructura anidada
            rows = self._extract_nested_repeat_data(submission, path_parts, questions, submission_id)  # _extraer_datos_repetidos_anidados

        return rows

    def _extract_nested_repeat_data(self, submission: Dict[str, Any], path_parts: List[str], questions: Dict[str, Any], submission_id: str) -> List[Dict[str, Any]]:  # _extraer_datos_repetidos_anidados, envio, partes_ruta, preguntas, id_envio
        """
        Extracts nested repeat group data using recursive navigation.
        Extrae datos de grupos repetidos anidados usando navegación recursiva.

        Args:
            submission: Complete submission data
            envio: Datos completos del envío
            path_parts: List with group names in hierarchical order
            partes_ruta: Lista con nombres de grupos en orden jerárquico
            questions: Questions belonging to this group
            preguntas: Preguntas que pertenecen a este grupo
            submission_id: Unique ID of parent submission
            id_envio: ID único del envío padre

        Returns:
            List of rows extracted from nested group
            Lista de filas extraídas del grupo anidado
        """
        rows = []  # filas

        # Manejar anidamiento de al menos 2 niveles
        if len(path_parts) >= 2:
            # NIVEL 1: Obtener elementos del primer grupo repetido
            # Ejemplo: si partes_ruta = ["grupo1", "grupo2"]
            # primer_nivel = envio["grupo1"] (lista de repeticiones)
            first_level = submission.get(path_parts[0], [])  # primer_nivel

            # Procesar cada elemento del primer nivel
            for i, first_item in enumerate(first_level):  # elemento_primer_nivel
                # Crear ID único para este elemento del primer nivel
                first_level_id = f"{submission_id}_{i + 1}"  # id_primer_nivel

                # Verificar si solo hay 2 niveles de anidamiento
                if len(path_parts) == 2:
                    # NIVEL 2: Construir clave para acceder al segundo nivel
                    # Ejemplo: "grupo1/grupo2"
                    second_level_key = f"{path_parts[0]}/{path_parts[1]}"  # clave_segundo_nivel

                    # Obtener elementos del segundo nivel dentro del elemento actual del primer nivel
                    second_items = first_item.get(second_level_key, [])  # elementos_segundo_nivel

                    # Procesar cada elemento del segundo nivel
                    for second_item in second_items:  # elemento_segundo
                        # Crear fila con referencias a ambos niveles padre
                        row = {  # fila
                            '_parent_id': submission_id,  # Referencia al envío original
                            f'_{path_parts[0]}_id': first_level_id  # Referencia al elemento del primer nivel
                        }

                        # Inicializar fila con columnas del grupo
                        self._initialize_row_for_group(row, questions)

                        # Llenar fila con datos del elemento del segundo nivel
                        self._fill_row_data(row, second_item)

                        # Agregar fila a la lista
                        rows.append(row)

        return rows

    def _initialize_row_for_group(self, row: Dict[str, Any], questions: Dict[str, Any]) -> None:  # _inicializar_fila_para_grupo, fila, preguntas
        """
        Initializes row with columns specific to a repeat group.
        Inicializa fila con columnas específicas de un grupo repetido.

        Args:
            row: Row dictionary to initialize (modified in place)
            fila: Diccionario de fila a inicializar (se modifica en el lugar)
            questions: Questions belonging to the group
            preguntas: Preguntas que pertenecen al grupo
        """
        # Agregar columna para cada pregunta del grupo
        for question in questions.values():  # pregunta
            # Usar nombre original como nombre de columna, inicializar en None
            row[question.original_name] = None

    def _get_sorted_repeat_groups(self) -> List[tuple]:  # _obtener_grupos_repetidos_ordenados
        """
        Gets repeat groups sorted by nesting level.
        Obtiene grupos repetidos ordenados por nivel de anidamiento.

        Returns:
            List of tuples (group_name, group_object) sorted by level
            Lista de tuplas (nombre_grupo, objeto_grupo) ordenada por nivel
            Example: [(level_0_group, obj), (level_1_group, obj), ...]
            Ejemplo: [(grupo_nivel_0, obj), (grupo_nivel_1, obj), ...]
        """
        return sorted(
            # Convertir diccionario a lista de tuplas
            self.structure.repeat_groups.items(),
            # Ordenar por el nivel de anidamiento (0, 1, 2, etc.)
            key=lambda x: x[1].level
        )
