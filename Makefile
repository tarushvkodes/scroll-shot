.PHONY: build-helper capture help self-test

help:
	@echo "Targets:"
	@echo "  build-helper  Compile the macOS native scroll helper"
	@echo "  capture       Run Scroll Shot from the source tree"
	@echo "  self-test     Run deterministic stitching self-test"

build-helper:
	mkdir -p bin
	swiftc platform/macos/ScrollShotScrollHelper.swift -o bin/scrollshot-scroll
	swiftc platform/macos/ScrollShotDetectHelper.swift -o bin/scrollshot-detect
	swiftc platform/macos/ScrollShotCountdownHelper.swift -o bin/scrollshot-countdown

capture: build-helper
	PYTHONPATH=src python3 -m scrollshot capture

self-test:
	PYTHONPATH=src python3 -m scrollshot self-test --output scroll-shot-self-test.png
