import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app_generator.validation.relative_velocity_derivation import emit_private_v8
parser=argparse.ArgumentParser()
for name in ("package","pdf","packets","corrections","out"):
    parser.add_argument("--"+name,type=Path,required=True)
a=parser.parse_args()
result=emit_private_v8(package_file=a.package,source_pdf=a.pdf,packets_file=a.packets,
                       corrections_file=a.corrections,out_dir=a.out)
print(json.dumps({k:v for k,v in result.items() if k not in ("exactInelasticWitness",)}))
