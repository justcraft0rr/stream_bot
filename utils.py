import requests
STREAMERBOT_URL = "http://127.0.0.1:7474/DoAction"


class sb:
    def run_action(action_id, **args):
        payload = {
            "action": {
                "id": action_id
            },
            "args": args
        }

        requests.post(
            STREAMERBOT_URL,
            json=payload
        )

    def twitch_message(sender, messagey: str, announce_color):
        if sender == "broadcaster":
            if announce_color is None:
                sb.run_action(
                    "4e371198-7606-4402-bbfd-9391bb004f7b",
                    message=messagey
                )
            elif announce_color == "blue":
                sb.run_action(
                    "80e077b8-13b7-41dc-ab72-8cfe28a44cee",
                    message=messagey
                )
            elif announce_color == "default":
                sb.run_action(
                    "e5773b55-8c83-417d-bf5d-badac167880a",
                    message=messagey
                )
            elif announce_color == "green":
                sb.run_action(
                    "12f29848-9fa5-4468-b0eb-cdb5c58704ff",
                    message=messagey
                )
            elif announce_color == "orange":
                sb.run_action(
                    "2091b5ef-b742-43b5-8df9-8c9133bf1885",
                    message=messagey
                )
            elif announce_color == "purple":
                sb.run_action(
                    "50d2b4a6-27da-4d27-83e6-1722162b1f70",
                    message=messagey
                )
        elif sender == "bot":
            if announce_color is None:
                sb.run_action(
                    "41deed2d-0616-42c1-a5ba-806e4e86fcf5",
                    message=messagey
                )
            elif announce_color == "blue":
                sb.run_action(
                    "7a86ec3c-1b07-4d88-937b-c994651747ab",
                    message=messagey
                )
            elif announce_color == "default":
                sb.run_action(
                    "aeccd193-30f9-4630-abed-9e82a455690b",
                    message=messagey
                )
            elif announce_color == "green":
                sb.run_action(
                    "a35c2723-9013-4ba5-8028-a9f774c6c983",
                    message=messagey
                )
            elif announce_color == "orange":
                sb.run_action(
                    "6feaaf73-f947-45b3-85e8-641cf17651aa",
                    message=messagey
                )
            elif announce_color == "purple":
                sb.run_action(
                    "e99b7f20-1746-462a-8e90-939d21c459cf",
                    message=messagey
                )

    def youtube_message(sender, messagey: str):
        if sender == "broadcaster":
            sb.run_action(
                "36e7fcbb-6d9d-4d5f-995b-3c99b135ac14",
                message=messagey
            )
        elif sender == "bot":
            sb.run_action(
                "8f57e65d-d3d0-4893-bbad-e395c6a41738",
                message=messagey
            )

    def global_message(sender, messagey: str, announce_color):
        sb.twitch_message(
            sender,
            messagey,
            announce_color
        )
        sb.youtube_message(
            sender,
            messagey
        )


class QOL:
    def read_file(file):
        return open(file, "r", encoding="utf-8").read()
