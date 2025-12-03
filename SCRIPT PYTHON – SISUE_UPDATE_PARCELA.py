# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# PROYECTO: MINAGRI - DGSEP
# Creado por: Francisco Calderón Franco
# Objetivo: UPDATE DE PARCELAS UE
# Descripción:
# Actualización de Geometrias de Empresas y campos
# Input: RUC
#
# ---------------------------------------------------------------------------

#--1.- Importamos las libreria
#--ArcPY
import arcpy
import sys
import datetime
import traceback

def printMessage(message):
    print("{}".format(message))
    arcpy.AddMessage(message)

def validar_fgdb(ruta):
    """Valida que la ruta exista y sea una file geodatabase válida."""
    if not os.path.exists(ruta):
        printMessage('==>{} - ERROR: Filegeodatabase - la ruta no existe'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        return False
    if not ruta.lower().endswith(".gdb"):
        printMessage('==>{} - ERROR: Filegeodatabase - La ruta no es una File Geodatabase'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        return False
    if not arcpy.Exists(ruta):
        printMessage('==>{} - ERROR: ArcPy no reconoce la geodatabase como válida'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        return False
    return True

def eliminar_registros_versionado(fc_destino, fc_destinoxy):
    """Elimina todos los registros de una tabla versionada usando UpdateCursor."""
    try:
        edit = arcpy.da.Editor(oPathGDB)
        edit.startEditing(False, True)
        with arcpy.da.UpdateCursor(fc_destino, ["OID@"]) as cursor:
            for row in cursor:
                cursor.deleteRow()
        with arcpy.da.UpdateCursor(fc_destinoxy, ["OID@"]) as cursor:
            for row in cursor:
                cursor.deleteRow()
        edit.stopEditing(True)
        printMessage('==>{} - [INFO] Registros eliminados correctamente'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    except Exception as e:
        printMessage('==>{} - [ERROR] No se pudo eliminar registros del destino: {}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),e))

def insertar_registros_XY(fc_origen, fc_destino):
    """Elimina todos los registros de una tabla versionada usando UpdateCursor."""
    try:
        spatial_ref = arcpy.SpatialReference(4326)
        edit = arcpy.da.Editor(oPathGDB)
        edit.startEditing(False, True)
        campos_cursor = ['NUM_CENTROIDE_X','NUM_CENTROIDE_Y','IDE_PARCELA_ORIGEN','IDE_PARCELA_CULTIVO','TXT_OBSERVACION_GENERAL','TXT_OBSERVACION_ESPECIFICA',
                         'TXT_DEPARTAMENTO','TXT_PROVINCIA','FEC_ULTIMA_ACTUALIZACION','FEC_USUARIO_REGISTRA','TXT_CULTIVO_ESPECIFICO','TXT_CULTIVO_GENERO','TXT_FECHA_REGISTRO']
        with arcpy.da.SearchCursor(fc_origen, campos_cursor) as cursor_lectura,\
             arcpy.da.InsertCursor(fc_destino, campos_cursor + ["SHAPE@"]) as cursor_escritura:
            for row in cursor_lectura:
                x = row[0]
                y = row[1]
                if x is None or y is None:
                    continue  # saltar si no hay coordenadas
                punto = arcpy.Point(x, y)
                geom = arcpy.PointGeometry(punto, spatial_ref)
                nueva_fila = row + (geom,)
                cursor_escritura.insertRow(nueva_fila)
        edit.stopEditing(True)
        printMessage('==>{} - [INFO] Registros insertado correctamente'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    except Exception as e:
        printMessage('==>{} - [ERROR] No se pudo insertar registros del destino: {}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),e))


try:
    #-1.- Parametros y variables
    #==>Variable de Input : Entorno
    oEnv = arcpy.GetParameterAsText(0)
    if oEnv == '#' or not oEnv:
        oRuc = 'DESA'  # provide a default value if unspecified

    #==>Variable de Input : ObjectID
    oRuc = arcpy.GetParameterAsText(1)
    if oRuc == '#' or not oRuc:
        oRuc = 6  # provide a default value if unspecified

    printMessage('==>{} - Paso 01: Configurando Variables'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    # ==>Define workspace de Salida
    oWksOutPut = "in_memory"
    oRspProc='N'

    # Ruta a la File Geodatabase
    ruta_fgdb = r"F:\\FCF\\SIGUE_PARCELA\\INPUT\\EUDR.gdb"
    # ==>FeatureClass
    oPathGDB = 'F:\\FCF\\GDB\\SISPOG_OPERADOR@10.55.73.12@SIEABD.sde'
    #--Obtenemos la ruta de los FeatureClass
    oFClassParcela = "{}\\SISPOG_OPERADOR.FDS_UNION_EUROPEA\\SISPOG_OPERADOR.FC_UE_PARCELA".format(oPathGDB)
    oFClassParcelaXY = "{}\\SISPOG_OPERADOR.FDS_UNION_EUROPEA\\SISPOG_OPERADOR.FC_UE_PARCELA_XY".format(oPathGDB)
    oFClassHistorico = "{}\\SISPOG_OPERADOR.FDS_UNION_EUROPEA\\SISPOG_OPERADOR.FC_UE_PARCELA_HISTORICO".format(oPathGDB)

    # Lista y procesa los Feature Classes dentro de la File GeodataAbase.
    printMessage('==>{} - Paso 02: Configurando FeatureClass Input'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    arcpy.env.workspace = ruta_fgdb
    oListFeatureClasses = arcpy.ListFeatureClasses()
    if not oListFeatureClasses:
        printMessage('==>{} - ERROR: No se encontraron feature classes en la geodatabase.'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        exit()

    # Leemos los FeatureClass
    for fc in oListFeatureClasses:
        try:
            # Lista de cambios: (campo_origen, nuevo_nombre, nuevo_alias)
            campos_a_renombrar = [
                ('IDE_PARCELAPOLIG', 'IDE_PARCELA_ORIGEN', 'IDE_PARCELA_ORIGEN'),
                ('IDE_ACTIV_CULTIVO', 'IDE_CULTIVO_ACTIVIDAD', 'IDE_CULTIVO_ACTIVIDAD'),
                ('IDE_CULTIVOESP', 'IDE_CULTIVO_ESPECIFICO', 'IDE_CULTIVO_ESPECIFICO'),

                ('NUM_ORDENCULTIVO', 'NUM_CULTIVO_ORDEN', 'NUM_CULTIVO_ORDEN'),
                ('ID_CULT', 'IDE_PARCELA_CULTIVO', 'IDE_PARCELA_CULTIVO'),
                ('IDE_ACTIV_PARCELA', 'IDE_PARCELA_ACTIVIDAD', 'IDE_PARCELA_ACTIVIDAD'),
                ('TXT_GPSLONGITUD', 'NUM_CENTROIDE_X', 'NUM_CENTROIDE_X'),
                ('TXT_GPSLATITUD', 'NUM_CENTROIDE_Y', 'NUM_CENTROIDE_Y'),
                ('AREA_SUPERFICIE', 'NUM_AREA_DECLARADA', 'NUM_AREA_DECLARADA'),
                ('AREA_UT_CULTIVO', 'NUM_AREA_CULTIVO', 'NUM_AREA_CULTIVO'),
                ('AREA_M2', 'NUM_AREA_M2', 'NUM_AREA_M2'),
                ('IDE_REGTENENCIA', 'IDE_REGIMEN_TENENCIA', 'IDE_REGIMEN_TENENCIA'),
                ('TENENCIA', 'TXT_REGIMEN_TENENCIA', 'TXT_REGIMEN_TENENCIA'),
                ('TXT_NRODOC', 'TXT_NUM_DOCUMENTO', 'TXT_NUM_DOCUMENTO'),
                ('TXT_APEPAT', 'TXT_APELLIDO_PATERNO', 'TXT_APELLIDO_PATERNO'),
                ('TXT_APEMAT', 'TXT_APELLIDO_MATERNO', 'TXT_APELLIDO_MATERNO'),
                ('TXT_CELULAR', 'TXT_NUM_CELULAR', 'TXT_NUM_CELULAR'),
                ('TXT_CULTIVOESP', 'TXT_CULTIVO_ESPECIFICO', 'TXT_CULTIVO_ESPECIFICO'),
                ('IDE_GENERO', 'IDE_CULTIVO_GENERO', 'IDE_CULTIVO_GENERO'),
                ('TXT_GENERO', 'TXT_CULTIVO_GENERO', 'TXT_CULTIVO_GENERO'),
                ('FUENTE', 'TXT_FUENTE_ORIGEN', 'TXT_FUENTE_ORIGEN'),
                ('OBSERVACION', 'TXT_OBSERVACION', 'TXT_OBSERVACION'),
                ('OBS_GRAL', 'TXT_OBSERVACION_GENERAL', 'TXT_OBSERVACION_GENERAL'),
                ('OBS_ESPECIF', 'TXT_OBSERVACION_ESPECIFICA', 'TXT_OBSERVACION_ESPECIFICA'),
                ('IDE_USUARIOREG', 'IDE_USUARIO_REGISTRA', 'IDE_USUARIO_REGISTRA'),
                ('FEC_REGISTRO', 'FEC_USUARIO_REGISTRA', 'FEC_USUARIO_REGISTRA'),
                ('DNI_PROMOTOR', 'TXT_PROMOTOR_DNI', 'TXT_PROMOTOR_DNI'),
                ('PROMOTOR', 'TXT_PROMOTOR_NOMBRES', 'TXT_PROMOTOR_NOMBRES'),
            ]
            # Obtener lista de campos existentes en el FC
            campos_existentes = [f.name for f in arcpy.ListFields(fc)]
            # Iterar y aplicar AlterField si existe el campo original
            for campo_viejo, campo_nuevo, alias_nuevo in campos_a_renombrar:
                if campo_viejo in campos_existentes:
                    try:
                        printMessage('==>{} - Paso 04: [INFO] Renombrando campo {} a {}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), campo_viejo,campo_nuevo))
                        arcpy.AlterField_management(fc, campo_viejo, campo_nuevo, alias_nuevo)
                    except Exception as e:
                        printMessage('==>{} - Paso 04: [ERROR] No se pudo renombrando campo {} a {} {}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), campo_viejo, campo_nuevo,e))
                else:
                    printMessage('==>{} - Paso 04: [WARN] Campo no encontrado : {} a {}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), campo_viejo, campo_nuevo))

        except Exception as e:
            printMessage('==>{} - ERROR: No se pudo procesar el FeatureClass {}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),e))

        #--Validamos que todos los campos existan
        printMessage('==>{} - Paso 05: Validando  campos del destino en el origen'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        # Obtener lista de campos existentes en el FC
        campos_existentes = [f.name for f in arcpy.ListFields(fc)]
        # Iterar y validar si existe el campo nuevo
        for campo_viejo, campo_nuevo, alias_nuevo in campos_a_renombrar:
            if not campo_nuevo in campos_existentes:
                printMessage('==>{} - Paso 05: [ERROR] No se encontro el campo {}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),campo_nuevo))
                exit()
        printMessage('==>{} - Paso 06: Actualizamos la fecha de carga'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        campo = "FEC_ULTIMA_ACTUALIZACION"
        if campo not in campos_existentes:
            arcpy.AddField_management(fc, campo, "DATE")
        arcpy.CalculateField_management(fc, "FEC_ULTIMA_ACTUALIZACION", 'datetime.datetime.now()', "PYTHON")
        campo = "TXT_FECHA_REGISTRO"
        if campo not in campos_existentes:
            arcpy.AddField_management(fc, campo, "TEXT",10)
        printMessage('==>{} - Paso 07: Actualizamos las coordenadas del centroide'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        campos_cursor = ["SHAPE@XY", "NUM_CENTROIDE_X", "NUM_CENTROIDE_Y",'FEC_USUARIO_REGISTRA',"TXT_FECHA_REGISTRO", "OBJECTID_1"]
        with arcpy.da.UpdateCursor(fc, campos_cursor) as cursor:
            for row in cursor:
                #print(row[5] )
                x, y = row[0]
                row[1] = x # x_centroide
                row[2] = y # y_centroide
                row[4] = row[3].strftime("%Y-%m-%d")
                cursor.updateRow(row)
        # Creamos el historico del FC_UE_PARCELA
        printMessage('==>{} - Paso 08: creamos el historicc'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        #arcpy.Append_management(oFClassParcela, oFClassHistorico, "NO_TEST")
        # Truncar el destino
        printMessage('==>{} - Paso 09: eliminamos los actuales registros'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        eliminar_registros_versionado(oFClassParcela,oFClassParcelaXY)
        printMessage('==>{} - Paso 10: Cargamos los nuevos registros'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        arcpy.Append_management(inputs=fc, target=oFClassParcela, schema_type="NO_TEST")
        printMessage('==>{} - Paso 11: Cargamos los nuevos registros XY'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        insertar_registros_XY(fc,oFClassParcelaXY)
        printMessage('==>{} - Fin del Proceso'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
except:
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
    # Return python error messages for use in script tool or Python window
    arcpy.AddError(pymsg)
    arcpy.AddError(msgs)
    # Print Python error messages for use in Python / Python window
    print(pymsg)
    print(msgs)