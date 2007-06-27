#!/usr/bin/python
from lamer import Lamer
from ConfigParser import RawConfigParser

class Identity:
    def __init__(self, data):
        self.name = data["name"]
        self.nicknames = data["nicknames"]
        self.password = data["password"]

class Channel:
    def __init__(self, data):
        self.name = data["name"]
        self.password = data["password"]

class Server:
    def __init__(self, data):
        self.port = int(data["port"])
        self.password = data["password"]
        self.server = data["server"]

    def __str__(self):
        return "%s:%s" % (self.server, self.port)

    def __repr__(self):
        return "<Server %s>" % self

class ServerGroup:
    def __init__(self, data):
        self.channels = set(data["autojoinchannels"].split(",")) | set(data["channelhistory"].split(","))
        self.name = data["name"]
        self.identity = data["identity"]
        if "serverlist" in data:
            self.server_list = data["serverlist"].split(",")
        else:
            self.server_list = []

class Konversation(Lamer):
    def __init__(self, verbose):
        Lamer.__init__(self, "konversation", verbose)

    def configDict(self, config, section):
        data = {}
        for key,value in config.items(section):
            key = unicode(key, "UTF-8")
            value = unicode(value, "UTF-8")
            data[key] = value
        return data

    def _extract(self):
        rc = self.open("~/.kde/share/config/konversationrc")
        config = RawConfigParser()
        config.readfp(rc)
        self.identities = {}
        self.channels = {}
        self.server_groups = {}
        self.servers = {}
        for section in config.sections():
            section = unicode(section, "UTF-8")
            server = None
            channel = None
            password = None
            if section.startswith("Channel "):
                data = self.configDict(config, section)
                try:
                    channel = Channel(data)
                    if channel.password:
                        self.channels[section] = channel
                except KeyError:
                    pass

            elif section.startswith("Identity "):
                data = self.configDict(config, section)
                try:
                    identity = Identity(data)
                    if identity.password:
                        self.identities[identity.name] = identity
                except KeyError:
                    pass

            elif section.startswith("ServerGroup "):
                data = self.configDict(config, section)
                try:
                    self.server_groups[section] = ServerGroup(data)
                except KeyError, err:
                    pass

            elif section.startswith("Server "):
                data = self.configDict(config, section)
                try:
                    self.servers[section] = Server(data)
                except KeyError:
                    pass

        for server_id, server_group in self.server_groups.iteritems():
            # Create server list
            servers = []
            if server_group.server_list:
                for server_id in server_group.server_list:
                    try:
                        server = self.servers[server_id]
                        servers.append(server)
                    except KeyError:
                        pass
            else:
                try:
                    server_id = "Server %s" % (server_id.split(" ",1)[1])
                    server = self.servers[server_id]
                    servers.append(server)
                except KeyError:
                    pass

            # Search identity
            try:
                identity = self.identities[server_group.identity]
            except LookupError:
                identity = None

            # Search channels
            channels = []
            for channel_id, channel in self.channels.iteritems():
                if channel_id in server_group.channels:
                    channels.append(channel)

            if not(identity or channels):
                continue
            if identity:
                self.dump(servers, 'identify -- nicknames=%s -- password=%s' % (identity.nicknames, identity.password))
            for channel in channels:
                self.dump(servers, "/join %s %s" % (channel.name, channel.password))

    def dump(self, servers, text):
        servers = ", ".join(str(item) for item in servers)
        self.write("%s: %s" % (servers, text))

Konversation(False).extract()

