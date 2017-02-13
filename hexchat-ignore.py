import hexchat
 
__module_name__        = "noevents"
__module_version__     = "1.0"
__module_description__ = "Ignores channel events messages"
 
def voice_event(word, word_eol, userdata):
    return hexchat.EAT_HEXCHAT
 
hexchat.hook_print("Channel Voice", voice_event)
hexchat.hook_print("Channel DeVoice", voice_event)
hexchat.hook_print("Channel Mode Generic", voice_event)
hexchat.hook_print("Channel Ban", voice_event)
hexchat.hook_print("Channel UnBan", voice_event)
