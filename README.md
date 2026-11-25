# DroneScript Entrega final

## Archivos
- `compiler.py`: lexer, parser, AST, reglas semanticas, tabla de simbolos, IR y optimizador de repeticion literal de una iteracion.
- `dronescript.lark`: gramatica. A diferencia del prototipo de Entrega 2, el bloque REPETIR exige al menos una instruccion (`instruction+`).
- `prueba_conductor.ds`: caso conductor usado para tokens, parseo, AST, semantica e IR.
- `optimizacion.ds`: ejemplo separado para comparar IR antes/despues.
- `error_lexico.ds`, `error_sintactico.ds`, `error_semantico.ds`: contraejemplos.
- `evidencia_*.txt`: capturas textuales de ejecuciones reales con Lark 1.3.1.
- `guion_video.md`: recorrido de 5-8 minutos.

## Ejecucion
Requiere Python 3.10 o superior.

```powershell
python -m pip install -r requirements.txt
python compiler.py prueba_conductor.ds
python compiler.py optimizacion.ds
python compiler.py error_lexico.ds
python compiler.py error_sintactico.ds
python compiler.py error_semantico.ds
```

Los dos errores lexicos/sintacticos retornan codigo 1. El caso semantico tambien retorna 1 luego de que lexer/parser aceptan su estructura. El caso conductor y la optimizacion retornan 0.

## Limites declarados
El analisis semantico implementa rangos de parametros y umbrales, pero no comprueba estados de vuelo, rutas, energia acumulada, tipos inferidos desde sensores reales ni seguridad fisica. La IR es una representacion didactica de tres direcciones; sus instrucciones de movimiento no son codigo ejecutable de un dron. El optimizador solo elimina un REPETIR con contador literal 1. No hay simulador de vuelo ni generacion de codigo de hardware.
