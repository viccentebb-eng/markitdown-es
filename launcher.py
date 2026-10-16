import sys

if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--convert-one":
        from markitdown_es.convert_one import main

        raise SystemExit(main(*sys.argv[2:]))
    if len(sys.argv) == 4 and sys.argv[1] == "--smoke-test":
        from scripts.smoke_test import run

        raise SystemExit(run(sys.argv[2], sys.argv[3]))
    from markitdown_es.__main__ import main

    raise SystemExit(main())
