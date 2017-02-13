import hexchat
 
__module_name__        = "noevents"
__module_version__     = "1.0"
__module_description__ = "Ignores channel events messages"
 
def voice_event(word, word_eol, userdata):
    return hexchat.EAT_HEXCHAT
 
ignore=[
  "Channel Voice",
  "Channel DeVoice",
  "Channel Mode Generic",
  "Channel Ban",
  "Channel UnBan",
  "Change Nick",
  "Kick"
] 

for i in ignore:
  hexchat.hook_print(i, voice_event)
