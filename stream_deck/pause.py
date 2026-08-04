import obsws_python as OBS_HANDLER
obs = OBS_HANDLER.ReqClient()

obs.toggle_record_pause()
obs.disconnect()
