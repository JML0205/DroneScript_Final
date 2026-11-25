"""Pipeline didactico de analisis y representacion para DroneScript."""
from pathlib import Path
import argparse, json, sys
from lark import Lark, Transformer, UnexpectedInput

ROOT = Path(__file__).resolve().parent
PARSER = Lark((ROOT / "dronescript.lark").read_text(encoding="utf-8-sig"), parser="lalr", lexer="basic", start="start", propagate_positions=True)
class BuildAST(Transformer):
    def start(self, xs): return {"tipo":"programa", "instrucciones":list(xs)}
    def takeoff(self, _): return {"tipo":"despegar"}
    def land(self, _): return {"tipo":"aterrizar"}
    def move(self, xs): return {"tipo":"mover", "direccion":str(xs[0]), "distancia":float(xs[1])}
    def turn(self, xs): return {"tipo":"girar", "grados":float(xs[0])}
    def wait(self, xs): return {"tipo":"esperar", "segundos":float(xs[0])}
    def conditional(self, xs): return {"tipo":"si", "sensor":str(xs[0]), "operador":str(xs[1]), "valor":float(xs[2]), "accion":xs[3]}
    def repeat(self, xs): return {"tipo":"repetir", "veces":int(xs[0]), "instrucciones":list(xs[1:])}

SYMBOLS = [
 {"nombre":"bateria","categoria":"sensor predefinido","tipo":"real","ambito":"global","dominio":"0..100 %"},
 {"nombre":"altura","categoria":"sensor predefinido","tipo":"real","ambito":"global","dominio":">= 0 m"},
 {"nombre":"ADELANTE/ATRAS/IZQUIERDA/DERECHA","categoria":"enumeracion","tipo":"direccion","ambito":"global","dominio":"valor de DIRECTION"},
]
def semantic(ast):
    errors=[]
    def check(x,where="instruccion"):
        t=x['tipo']
        if t=='mover' and x['distancia']<=0: errors.append(f"{where}: la distancia debe ser mayor que 0")
        elif t=='girar' and not 0<=x['grados']<=360: errors.append(f"{where}: los grados deben estar entre 0 y 360")
        elif t=='esperar' and x['segundos']<0: errors.append(f"{where}: los segundos no pueden ser negativos")
        elif t=='si':
            limit=100 if x['sensor']=='bateria' else None
            if x['valor']<0 or (limit is not None and x['valor']>limit): errors.append(f"{where}: umbral fuera del dominio del sensor {x['sensor']}")
            check(x['accion'],"accion de SI")
        elif t=='repetir':
            if x['veces']<1: errors.append(f"{where}: REPETIR requiere al menos 1 iteracion")
            for i,y in enumerate(x['instrucciones'],1): check(y,f"instruccion {i} del bloque")
    for i,x in enumerate(ast['instrucciones'],1): check(x,f"instruccion {i}")
    return errors

def emit_ir(ast):
    out=[]; temp=0; label=0
    def T():
        nonlocal temp; temp+=1; return f"t{temp}"
    def L():
        nonlocal label; label+=1; return f"L{label}"
    def seq(xs):
        for x in xs: emit(x)
    def emit(x):
        t=x['tipo']
        if t in ('despegar','aterrizar'): out.append(('DESPEGAR' if t=='despegar' else 'ATERRIZAR'))
        elif t=='mover': out.append(f"MOVER {x['direccion']} {x['distancia']:g}")
        elif t=='girar': out.append(f"GIRAR {x['grados']:g}")
        elif t=='esperar': out.append(f"ESPERAR {x['segundos']:g}")
        elif t=='si':
            end=L(); out.append(f"IF NOT ({x['sensor']} {x['operador']} {x['valor']:g}) GOTO {end}"); emit(x['accion']); out.append(f"{end}:")
        elif t=='repetir':
            counter=T(); start=L(); end=L(); out.append(f"{counter} = 0"); out.append(f"{start}:"); out.append(f"IF {counter} >= {x['veces']} GOTO {end}"); seq(x['instrucciones']); out.append(f"{counter} = {counter} + 1"); out.append(f"GOTO {start}"); out.append(f"{end}:")
    seq(ast['instrucciones']); return out

def optimize_once(ast):
    """Expande REPETIR 1: misma secuencia observable, sin contador/saltos."""
    def rewrite(x):
        if x['tipo']=='repetir':
            body=[]
            for y in x['instrucciones']: body.extend(rewrite(y))
            if x['veces']==1: return body
            return [{**x,'instrucciones':body}]
        return [x]
    out=[]
    for x in ast['instrucciones']: out.extend(rewrite(x))
    return {"tipo":"programa","instrucciones":out}
def analyze(src):
    toks=list(PARSER.lex(src)); tree=PARSER.parse(src); ast=BuildAST().transform(tree); return toks,tree,ast

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('archivo',nargs='?'); ap.add_argument('--solo-tokens',action='store_true'); ap.add_argument('--sin-opt',action='store_true'); a=ap.parse_args()
    src=Path(a.archivo).read_text(encoding='utf-8') if a.archivo else sys.stdin.read()
    try: toks,tree,ast=analyze(src)
    except UnexpectedInput as e:
        print(f"Error de analisis en linea {e.line}, columna {e.column}.",file=sys.stderr); print(e.get_context(src),file=sys.stderr); return 1
    print('TOKENS')
    for t in toks: print(f"{t.type:<10} {str(t)!r} (linea {t.line}, columna {t.column})")
    if a.solo_tokens: return 0
    print('\nARBOL SINTACTICO'); print(tree.pretty()); print('AST'); print(json.dumps(ast,ensure_ascii=False,indent=2))
    errs=semantic(ast); print('\nANALISIS SEMANTICO')
    for s in SYMBOLS: print(f"{s['nombre']} | {s['categoria']} | {s['tipo']} | ambito={s['ambito']} | dominio={s['dominio']}")
    if errs:
        for e in errs: print('ERROR:',e)
        return 1
    print('Resultado: valido segun las reglas semanticas implementadas.')
    ir=emit_ir(ast); print('\nIR SIN OPTIMIZAR'); print('\n'.join(ir) or '(vacia)')
    if not a.sin_opt:
        optimized=optimize_once(ast); optir=emit_ir(optimized); print('\nIR OPTIMIZADA'); print('\n'.join(optir) or '(vacia)')
    return 0
if __name__=='__main__': raise SystemExit(main())


