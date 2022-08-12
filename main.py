import argparse
import json
import logging

import asyncio
import typing

import tornado.web

import ts3_api
import handlers


async def main(listen_addresses: typing.List[str], listen_port: int, api: ts3_api.TeamSpeak3ServerAPI):
	app = tornado.web.Application([
		(r"/state", handlers.StateHandler, {"api": api}),
		(r"/clients/online", handlers.OnlineClientsHandler, {"api": api}),
		(r"/clients/online/(\d+)", handlers.OnlineClientInfoHandler, {"api": api}),
		(r"/clients/known", handlers.KnownClientsHandler, {"api": api}),
		(r"/clients/known/(\d+)", handlers.KnownClientInfoHandler, {"api": api}),
	])

	for listen_address in listen_addresses:
		app.listen(listen_port, listen_address)

	await asyncio.Event().wait()


def get_cli_args():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--config", "-c", default="config.json",
		help="Path to the configuration JSON file for the exporter."
	)
	parser.add_argument("--verbose", "-v", action="store_true", help="Be verbose about what is done.")
	parser.add_argument("--debug", "-d", action="store_true", help="Output debug information (implies -v).")

	return parser.parse_args()


def setup_logging(verbose: bool, debug: bool):
	if debug:
		log_level = logging.DEBUG
	elif verbose:
		log_level = logging.INFO
	else:
		log_level = logging.WARNING

	logging.basicConfig(
		level=log_level,
		format="[%(asctime)s] %(levelname)8s: %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S"
	)


def load_config(config_path: str):
	with open(config_path, "r") as config_fh:
		return json.load(config_fh)


def setup_ts3_api(host: str, scheme: str, port: int, virtual_server_id: int, token: str):
	api = ts3_api.TeamSpeak3ServerAPI(host, scheme, port, virtual_server_id, token)

	version_data = api.get_version()
	logging.info(f"Connected to TeamSpeak3 Server at {host} ({version_data['platform']}, {version_data['version']})")

	return api


if __name__ == "__main__":
	args = get_cli_args()
	setup_logging(args.verbose, args.debug)
	config = load_config(args.config)
	ts3_api = setup_ts3_api(
		config["api"]["server_hostname"],
		config["api"]["scheme"],
		config["api"]["webquery_port"],
		config["api"]["virtual_server_id"],
		config["api"]["webquery_token"]
	)
	asyncio.run(main(config["server"]["listen_addresses"], config["server"]["listen_port"], ts3_api))
