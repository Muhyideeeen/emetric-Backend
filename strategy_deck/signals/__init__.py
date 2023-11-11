from .initiative import (
    post_save_initiative_receiver,
    post_delete_initiative_receiver,
    pre_save_initiative_receiver
)
from .objective import (
    post_save_objective_receiver,
    pre_save_objective_receiver,
    post_delete_objective_receiver,
)
from .objective_perspective_spread import (
    post_delete_objective_perspective_spread_receiver,
)
from .perspective import (
    post_delete_perspective_receiver,
    post_save_perspective_receiver,
)
