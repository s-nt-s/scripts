import hexchat
 
__module_name__        = "noevents"
__module_version__     = "1.0"
__module_description__ = "Ignores channel events messages"

def not_ignore():
  if not hexchat.get_info("channel"):
    return True
  return len(hexchat.get_list("users"))<=100

def voice_event(word, word_eol, userdata):
  if not_ignore():
    return hexchat.EAT_NONE
  return hexchat.EAT_HEXCHAT
 
ignore=[
  "Channel Voice",
  "Channel DeVoice",
  "Channel Mode Generic",
  "Channel Ban",
  "Channel UnBan",
  "Channel Operator",
  "Channel Remove Invite",
  "Channel INVITE",
  "Channel Mode Generic",
  "Channel Half-Operator",
  "Channel DeHalfOp",
  "Channel DeOp",
  "Channel Exempt",
  "Channel Quiet",
  "Change Nick",
  "Kick"
] 

for i in ignore:
  hexchat.hook_print(i, voice_event)
