from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete, pre_save


class StrategyDeckConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "strategy_deck"

    def ready(self) -> None:
        from strategy_deck.models import (
            Initiative,
            Objective,
            ObjectivePerspectiveSpread,
            Perspective,
        )
        from strategy_deck.signals import (
            post_save_initiative_receiver,
            post_delete_initiative_receiver,
            post_save_objective_receiver,
            pre_save_objective_receiver,
            post_delete_objective_receiver,
            post_delete_objective_perspective_spread_receiver,
            post_save_perspective_receiver,
            post_delete_perspective_receiver,
            pre_save_initiative_receiver,
        )

        post_save.connect(post_save_initiative_receiver, sender=Initiative)
        post_delete.connect(post_delete_initiative_receiver, sender=Initiative)
        pre_save.connect(pre_save_initiative_receiver, sender=Initiative)

        post_save.connect(post_save_objective_receiver, sender=Objective)
        pre_save.connect(pre_save_objective_receiver, sender=Objective)
        post_delete.connect(post_delete_objective_receiver, sender=Objective)

        post_delete.connect(
            post_delete_objective_perspective_spread_receiver,
            sender=ObjectivePerspectiveSpread,
        )

        post_save.connect(post_save_perspective_receiver, sender=Perspective)

        post_delete.connect(
            post_delete_perspective_receiver,
            sender=Perspective,
        )
        return super().ready()
