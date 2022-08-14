import json
import re
import typing

import requests


class TS3APIInternalError(Exception):
	pass


class TS3APINotFoundError(Exception):
	pass


class TS3APIBadRequestError(Exception):
	pass


class TeamSpeak3ServerAPI:
	def __init__(self, host: str, scheme: str, port: int, virtual_server_id: int, token: str):
		self.host = host
		self.scheme = scheme
		self.port = port
		self.virtual_server_id = virtual_server_id
		self.token = token

	def do_request(self, path: str, query_params: typing.Dict[str, str] = None):
		cleaned_path = path
		if path.startswith("/"):
			cleaned_path = re.sub(r"^/+", "", path)

		auth_header = {"x-api-key": self.token}
		response = requests.get(
			f"{self.scheme}://{self.host}:{self.port}/{cleaned_path}",
			headers=auth_header,
			params=query_params
		)

		try:
			data = response.json()
		except json.JSONDecodeError as jde:
			raise TS3APIInternalError(f"Failed to decode TeamSpeak3 server response as JSON: {jde}")

		status = data.get("status")
		if status is None:
			raise TS3APIInternalError("TeamSpeak3 server JSON response did not contain the request status info.")

		status_code = status.get("code")
		if status_code is None:
			raise TS3APIInternalError("TeamSpeak3 server JSON response status info did not contain the status code.")

		if status_code != 0:
			if status_code in [512]:
				raise TS3APINotFoundError(f"{status_code} ({status.get('message', '')})")
			else:
				raise TS3APIBadRequestError(f"Request to TS3 WebQuery API failed: {status_code} ({status.get('message', '')})")

		body = data.get("body")
		if body is None:
			raise TS3APIInternalError("TeamSpeak3 server JSON response did not contain the expected 'body' key.")

		return body

	def do_request_with_single_object_response(self, path: str, query_params: typing.Dict[str, str] = None):
		response = self.do_request(path, query_params)

		if len(response) > 1:
			raise TS3APIInternalError(f"Unexpectedly got more than one object in response.")
		elif len(response) == 0:
			raise TS3APINotFoundError(f"No data found for request.")

		return response[0]

	def get_version(self):
		return self.do_request(f"/version")[0]

	def get_channel_list(self) -> typing.List[typing.Dict[str, str]]:
		query_params = {
			"-flags": "",
			"-limits": "",
			"-secondsempty": ""
		}
		channel_list = self.do_request(f"/{self.virtual_server_id}/channellist", query_params)

		for channel in channel_list:
			# Replace cid with channel_id as it is more intuitive
			channel["channel_id"] = channel["cid"]
			del channel["cid"]

		return channel_list

	def get_online_clients(self) -> typing.List[typing.Dict[str, str]]:
		query_params = {
			"-away": "",
			"-voice": "",
			"-times": "",
			"-groups": "",
			"-country": ""
		}
		online_clients = self.do_request(f"/{self.virtual_server_id}/clientlist", query_params)

		# Replace cid and clid by channel_id and online_client_id as it is more intuitive
		# Also, replace client_database_id with known_client_id for consistency
		for online_client in online_clients:
			online_client["channel_id"] = online_client["cid"]
			del online_client["cid"]

			online_client["online_client_id"] = online_client["clid"]
			del online_client["clid"]

			online_client["known_client_id"] = online_client["client_database_id"]
			del online_client["client_database_id"]

		return online_clients

	def get_known_clients(self) -> typing.List[typing.Dict[str, str]]:
		max_clients_per_page = 25
		num_clients_in_page = max_clients_per_page

		known_clients = []
		while num_clients_in_page == max_clients_per_page:
			query_params = {"start": str(len(known_clients))}
			clients_in_page = self.do_request(f"/{self.virtual_server_id}/clientdblist", query_params)
			known_clients.extend(clients_in_page)
			num_clients_in_page = len(clients_in_page)

		# Replace cldbid with known_client_id as it is more intuitive
		for known_client in known_clients:
			known_client["known_client_id"] = known_client["cldbid"]
			del known_client["cldbid"]

		return known_clients

	def get_online_client_info(self, online_client_id: str):
		online_client = self.do_request_with_single_object_response(
			f"/{self.virtual_server_id}/clientinfo",
			{"clid": online_client_id}
		)

		# Replace cid by channel_id as it is more intuitive
		online_client["channel_id"] = online_client["cid"]
		del online_client["cid"]

		return online_client

	def get_known_client_info(self, known_client_id: str):
		return self.do_request_with_single_object_response(
			f"/{self.virtual_server_id}/clientdbinfo",
			{"cldbid": known_client_id}
		)

	def get_server_name_description(self):
		server_info = self.do_request(f"/{self.virtual_server_id}/serverinfo")[0]
		return server_info["virtualserver_name"], server_info["virtualserver_welcomemessage"]

	def get_channel_info(self, channel_id: str):
		return self.do_request_with_single_object_response(
			f"/{self.virtual_server_id}/channelinfo",
			{"cid": channel_id}
		)
