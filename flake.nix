{
  description = "Self-contained pinned Jolt/Chez/Slipstream Wasm build (Linux x86_64)";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    jolt = {
      url = "git+https://github.com/jolt-lang/jolt.git?rev=5b46858a171f30949f5b09eb484bc6c5ff93c6ea&submodules=1";
      flake = false;
    };
    chezScheme = {
      url = "git+https://github.com/cisco/ChezScheme.git?rev=7fadeee45fcc0135b17f5c1a926157004f898339&submodules=1";
      flake = false;
    };
  };
  outputs = { self, nixpkgs, jolt, chezScheme }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      pinnedJolt = pkgs.stdenv.mkDerivation {
        pname = "jolt";
        version = "5b46858a";
        src = jolt;
        strictDeps = true;
        nativeBuildInputs = [ pkgs.chez pkgs.makeWrapper pkgs.pkg-config pkgs.xxd ];
        buildInputs = [ pkgs.lz4 pkgs.zlib pkgs.ncurses pkgs.openssl pkgs.libuuid ];
        dontConfigure = true;
        buildPhase = "scheme --script host/chez/build-jolt.ss release target/release/jolt";
        installPhase = ''
          install -Dm755 target/release/jolt "$out/bin/jolt"
          wrapProgram "$out/bin/jolt" \
            --prefix PATH : "${pkgs.lib.makeBinPath [ pkgs.git pkgs.unzip ]}" \
            --set-default JOLT_OPENSSL_LIBDIR "${pkgs.lib.makeLibraryPath [ pkgs.openssl ]}" \
            --set-default SSL_CERT_FILE "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
        '';
      };
    in {
      packages.${system} = {
        jolt = pinnedJolt;
        i686-cc = pkgs.pkgsi686Linux.stdenv.cc;
      };
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [ bash chez chromium cmake curl emscripten file
          gnumake git nodejs ninja pinnedJolt pkg-config patch python3 xxd unzip ];
        shellHook = ''
          export JOLT_SOURCE=${jolt}
          export CHEZ_SOURCE=${chezScheme}
          export JOLT_UPSTREAM_REVISION=5b46858a171f30949f5b09eb484bc6c5ff93c6ea
          export CHEZ_UPSTREAM_REVISION=7fadeee45fcc0135b17f5c1a926157004f898339
          # A pinned font avoids depending on the host workstation's font install.
          if [ -z "''${WEB_FONT:-}" ]; then
            export WEB_FONT=${pkgs.dejavu_fonts}/share/fonts/truetype/DejaVuSansMono.ttf
            export WEB_FONT_LICENSE=${pkgs.dejavu_fonts.full-ttf.src}/LICENSE
          fi
        '';
      };
    };
}
