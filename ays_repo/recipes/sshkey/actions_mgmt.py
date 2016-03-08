from JumpScale import j

ActionsBase = j.atyourservice.getActionsBaseClassMgmt()


class Actions(ActionsBase):

    def _generateKey(self):
        name = "key_%s" % self.service.hrd.getStr('key.name')
        keyfile = j.do.joinPaths(self.service.path, name)
        j.do.delete(keyfile)
        j.do.delete(keyfile + ".pub")
        cmd = "ssh-keygen -t rsa -f %s -P '%s' " % (keyfile, self.service.hrd.getStr('key.passphrase'))
        print(cmd)
        j.sal.process.executeWithoutPipe(cmd)

        if not j.sal.fs.exists(path=keyfile):
            raise RuntimeError("cannot find path for key %s, was keygen well executed" % keyfile)

        privkey = j.do.readFile(keyfile)
        pubkey = j.do.readFile(keyfile + ".pub")

        return privkey, pubkey

    def _checkAgent(self):
        rc, out = j.do.execute("ssh-add -l", outputStdout=False, outputStderr=False, dieOnNonZeroExitCode=False)
        
        # is running
        if rc == 0:
            return True
        
        # running but no keys
        if rc == 1:
            return True
        
        # another error
        return False
    
    def _startAgent(self):
        # FIXME
        j.do.execute("ssh-agent", dieOnNonZeroExitCode=False, outputStdout=False, outputStderr=False)

    def hrd(self):
        """
        create key
        """
        if self.service.hrd.get("key.name")=="":
            self.service.hrd.set("key.name",self.service.instance)
        
        name = "key_%s" % self.service.hrd.getStr('key.name')

        # if '$(key.passphrase)'=="":
        print("generate key")
        privkey, pubkey = self._generateKey()

        self.service.hrd.set("key.priv", privkey)
        self.service.hrd.set("key.pub", pubkey)
        
        if self.service.hrd.get("required") and not self._checkAgent():
            # print("agent not started")
            # self._startAgent()
            raise RuntimeError("ssh-agent is not running and you need it, please run: eval $(ssh-agent -s)")

        try:
            keyloc = j.do.getSSHKeyPathFromAgent(name, die=False)
        except:
            keyloc = None

        if keyloc is None:
            keyloc = j.do.joinPaths(self.service.path, name)

        j.do.chmod(keyloc, 0o600)

        keyfile = j.do.joinPaths(self.service.path, name)
        if not j.sal.fs.exists(path=keyfile):
            raise RuntimeError("could not find sshkey:%s" % keyfile)

        if j.do.getSSHKeyPathFromAgent(name, die=False) is None:
            cmd = 'ssh-add %s' % keyfile
            j.do.executeInteractive(cmd)

    def install_post(self):
        self.start()
        return True

    def _getKeyPath(self):
        keyfile = j.do.joinPaths(self.service.path, "key_$(key.name)")
        if not j.sal.fs.exists(path=keyfile):
            raise RuntimeError("could not find sshkey:%s" % keyfile)
        return keyfile

    def start(self):
        """
        Add key to SSH Agent if not already loaded
        """
        keyfile = self._getKeyPath()
        if j.do.getSSHKeyPathFromAgent("$(key.name)", die=False) is None:
            cmd = 'ssh-add %s' % keyfile
            j.do.executeInteractive(cmd)

    def stop(self):
        """
        Remove key from SSH Agent
        """
        keyfile = self._getKeyPath()
        if j.do.getSSHKeyPathFromAgent('$(key.name)', die=False) is not None:
            keyloc = "/root/.ssh/%s" % '$(key.name)'
            cmd = 'ssh-add -d %s' % keyfile
            j.do.executeInteractive(cmd)

    def removedata(self):
        """
        remove key data
        """
        keyfile = self._getKeyPath(self.service)
        j.delete(keyfile)
        j.delete(keyfile + ".pub")
