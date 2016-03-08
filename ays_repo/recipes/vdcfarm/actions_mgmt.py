import hashlib
from JumpScale import j

ActionsBase = j.atyourservice.getActionsBaseClassMgmt()


class Actions(ActionsBase):

    def getClient(self):
        openvcloudClient = j.clients.openvcloud.get('$(apiurl)', '$(login)', '$(passwd)')
        return openvcloudClient
