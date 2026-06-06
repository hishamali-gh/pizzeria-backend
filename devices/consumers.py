import json

from channels.generic.websocket import AsyncWebsocketConsumer

class TelemetryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.device_id = self.scope['url_route']['kwargs']['device_id']

        self.group_name = f"telemetry_{self.device_id}"

        # Join the Redis "Room" for this specific device
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # This method is called when we want to SHOUT data to the HMI
    async def telemetry_message(self, event):
        await self.send(text_data=json.dumps({
            'value': event['value'],
            'status': event['status']
        }))

    async def device_command(self, event):
        """
        No-op handler to absorb the control commands broadcast to this channel.
        This prevents Django Channels from raising an AttributeError and killing the WebSocket.
        """
        pass
