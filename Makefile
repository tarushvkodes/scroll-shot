.PHONY: build-helper capture help

help:
	@echo "Targets:"
	@echo "  build-helper  Compile the macOS native scroll helper"
	@echo "  capture       Run Scroll Shot from the source tree"

build-helper:
	mkdir -p bin
	swiftc platform/macos/ScrollShotScrollHelper.swift -o bin/scrollshot-scroll

capture: build-helper
	PYTHONPATH=src python3 -m scrollshot
