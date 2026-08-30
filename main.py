"""Simulation-first environmental resource management dashboard."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from decision_engine import build_decision
from environmental_simulator import EnvironmentalSimulator

ROOT = Path(__file__).parent
simulator = EnvironmentalSimulator()
resources = [
	{"name": "Water", "quantity": 420, "unit": "L", "priority": 10},
	{"name": "Food", "quantity": 160, "unit": "kg", "priority": 7},
	{"name": "Fuel", "quantity": 85, "unit": "L", "priority": 6},
	{"name": "General supplies", "quantity": 34, "unit": "boxes", "priority": 5},
]


class DashboardHandler(BaseHTTPRequestHandler):
	def send_json(self, payload, status=200):
		body = json.dumps(payload).encode("utf-8")
		self.send_response(status)
		self.send_header("Content-Type", "application/json")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def do_GET(self):
		route = urlparse(self.path).path
		if route == "/":
			body = (ROOT / "dashboard.html").read_bytes()
			self.send_response(200)
			self.send_header("Content-Type", "text/html; charset=utf-8")
			self.send_header("Content-Length", str(len(body)))
			self.end_headers()
			self.wfile.write(body)
		elif route == "/api/status":
			self.send_json(build_decision(simulator.snapshot(), resources))
		else:
			self.send_error(404)

	def do_POST(self):
		route = urlparse(self.path).path
		if route == "/api/resources":
			length = int(self.headers.get("Content-Length", 0))
			submitted = json.loads(self.rfile.read(length))
			if not isinstance(submitted, list) or not all(isinstance(item, dict) for item in submitted):
				self.send_json({"error": "Resources must be a list."}, 400)
				return
			resources[:] = submitted
			self.send_json(build_decision(simulator.snapshot(), resources))
			return
		if route != "/api/refresh":
			self.send_error(404)
			return
		simulator.advance()
		self.send_json(build_decision(simulator.snapshot(), resources))

	def log_message(self, format, *args):
		return


def run(host=None, port=None):
	host = host or os.environ.get("HOST", "0.0.0.0")
	port = int(port or os.environ.get("PORT", "8000"))
	try:
		server = ThreadingHTTPServer((host, port), DashboardHandler)
	except OSError as error:
		raise OSError(
			f"Could not bind dashboard to {host}:{port}. "
			"Set PORT to an available port or stop the process using it."
		) from error
	print(f"Island resource dashboard: http://{host}:{port}")
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		print("\nDashboard stopped.")
	finally:
		server.server_close()


if __name__ == "__main__":
	run()