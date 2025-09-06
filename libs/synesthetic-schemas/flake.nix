{
  description = "A simple and resilient development environment for the synesthetic-schemas project";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: let
    systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
    forAllSystems = nixpkgs.lib.genAttrs systems;
  in {
    devShells = forAllSystems (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        default = pkgs.mkShell {
          buildInputs = [
            pkgs.python311
            # The Fix: The attribute name is 'python3', not 'python'.
            (pkgs.poetry.override { python3 = pkgs.python311; })
            pkgs.nodejs_20
          ];

          shellHook = ''
            poetry config virtualenvs.in-project true --local
            unset VIRTUAL_ENV

            echo ""
            echo "--- Synesthetic Schemas Development Environment ---"
            echo "Nix has provided: Python, Poetry (pinned to Python 3.11), and Node.js."
            echo ""
            echo "To set up, run 'poetry install' to create the .venv and install dependencies."
            echo "Then, run './build.sh' to generate and validate all artifacts."
            echo "-------------------------------------------------"
            echo ""
          '';
        };
      });
  };
}