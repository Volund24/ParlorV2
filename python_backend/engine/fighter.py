import discord

class AvatarProxy:
    def __init__(self, url):
        self.url = url

class Fighter:
    def __init__(self, member, custom_url=None):
        self.member = member
        self.custom_url = custom_url
        
    @property
    def display_name(self):
        return self.member.display_name
        
    @property
    def mention(self):
        return self.member.mention
        
    @property
    def id(self):
        return self.member.id
        
    @property
    def name(self):
        return self.member.name

    @property
    def display_avatar(self):
        if self.custom_url:
            return AvatarProxy(self.custom_url)
        return self.member.display_avatar
        
    def __eq__(self, other):
        if isinstance(other, Fighter):
            return self.member.id == other.member.id
        if isinstance(other, discord.Member):
            return self.member.id == other.id
        return False
