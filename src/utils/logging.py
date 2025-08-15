import logging

LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(phase)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

class PhaseLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that ensures a 'phase' attribute exists for formatting."""
    def process(self, msg, kwargs):
        extra = kwargs.setdefault('extra', {})
        if 'phase' not in extra:
            extra['phase'] = self.extra.get('phase', 'GENERAL')
        return msg, kwargs

def get_logger(name: str = __name__, default_phase: str = 'GENERAL') -> PhaseLoggerAdapter:
    """Return a logger configured with a default phase."""
    logger = logging.getLogger(name)
    return PhaseLoggerAdapter(logger, {'phase': default_phase})
