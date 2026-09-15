.PHONY: demo test clean

demo:          ## replay traffic through the sensor, then show what the agent sees
	cd prototype && python3 demo_app.py
	cd prototype && python3 -m hud_lite.mcp_server --data .hud-demo/runtime.json --demo

test:          ## run the prototype self-checks
	cd prototype && python3 -m unittest test_prototype -v

clean:
	rm -rf prototype/.hud-demo prototype/__pycache__ prototype/hud_lite/__pycache__
