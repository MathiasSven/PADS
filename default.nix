{ pkgs ? import <nixpkgs> { } }:

let
  inherit (pkgs) python312Packages git;
in

python312Packages.buildPythonPackage {
  name = "pads";
  pyproject = true;
  src = ./.;

  build-system = with python312Packages; [
    setuptools
    versioningit
    git
  ];
  
  checkPhase = ''
    runHook preCheck

    declare -A skip=(
    )
    for pyfile in $(grep -l unittest PADS/*.py); do
      local filename=$(basename "$pyfile" .py)

      if [[ -v skip["$filename"] ]]; then
        echo "!!! Skipping tests for \"$filename\""
        echo
        continue
      fi

      echo ">>> Running tests for \"$filename\""
      python -m "PADS.''${filename}"
      echo
    done

    runHook postCheck
  '';

  pythonImportsCheck = [ "PADS.AcyclicReachability" ];
}
