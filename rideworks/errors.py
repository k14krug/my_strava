"""Expected import and evidence failures."""


class RideWorksError(Exception):
    pass


class IntegrityError(RideWorksError):
    pass


class InvalidFitError(RideWorksError):
    pass
