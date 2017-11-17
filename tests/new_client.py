


class Client(object):

    def __init__(self, dsn=Ellipsis, *args, **kwargs):

        self.dsn = dsn
        self.environment = Environ()  # singleton encapsulating lazy? system properties
        self.settings = Settings(dsn, *args, **kwargs)  # kwargs settings > os.environ variables > defaults
        self.transport = self.get_transport()
        self.instrument()
        self.spool = self.get_spool() # in-memory, to-disk, etc...

    def get_interfaces(self, **kwargs): # returns list of callables
        return self.settings.get('interfaces')

    def get_instrumentation_hooks(self, **kwargs): # returns list of callables
        return self.settings.get('instrument_hooks')

    def get_validators(self, **kwargs): # returns list of callables
        return self.settings.get('validators')

    def get_default_message(self, **kwargs): # returns dictionary
        return self.settings.get('message_data')

    def instrument(self, force=False):
        if self.environment.instrumented or force:
            for hook in self.get_instrument_hooks():
                try:
                    hook()
                except Exception:
                    # log.warn("Configuration bla bla...")
                    self.sys_warnings.append({"type": "sys_hook", "message":"Hook ... failed. ")


    def capture_exception(self, exception, **kwargs):
        message = Message(exception, defaults=self.get_default_message(), **kwargs)
        for interface in self.get_interfaces(**kwargs):
            try:
                message = interface.process(message, self.settings, self.environment)
            except Exception as e:
                message.add_error(interface, e)

        for validator in self.get_validators(**kwargs):
            try:
                message = validator.process(message, self.settings, self.environment)
            except ValidationError:
                pass # maybe we can fix it here, purge the offending interface, etc.. ?
            except Exception:
                message.add_error(validator, e)

        try:
            message.send(transport=self.transport, sys_warnings=self.sys_warnings)
        except NetworkException:
            message.retry = True
            self.spool.add(message)
        except Exception:
            # add to sys warnings?
            self.sys_warnings.append({"type":"transport_failed", "message": "Some messages are failing, check logs")








