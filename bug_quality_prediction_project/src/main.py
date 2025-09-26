
import argparse
from pathlib import Path
from .pipeline import run_dataset, cross_project_eval

def main():
    parser = argparse.ArgumentParser(description="Bug Prediction & Code Quality Scoring")
    parser.add_argument('--data', type=str, required=True, help='Path to CSV dataset')
    parser.add_argument('--out', type=str, required=True, help='Output directory')
    parser.add_argument('--cross', action='store_true', help='Run cross-project evaluation (expects kc1,jm1,pc1 in same folder)')
    args = parser.parse_args()
    if args.cross:
        paths = {'kc1': Path(Path(args.data).parent/'kc1.csv'),
                 'jm1': Path(Path(args.data).parent/'jm1.csv'),
                 'pc1': Path(Path(args.data).parent/'pc1.csv')}
        cross_project_eval(paths, Path(args.out)/'cross_project')
    else:
        run_dataset(Path(args.data), Path(args.out))

if __name__ == '__main__':
    main()
