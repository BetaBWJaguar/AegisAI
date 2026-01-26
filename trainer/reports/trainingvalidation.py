from trainer.reports.report_config import TrainingConfig


class TrainingConfigValidationError(ValueError):
    pass


class TrainingConfigValidator:

    @classmethod
    def validate(cls, config: TrainingConfig) -> None:
        errors = []

        cls._validate_hours(config, errors)
        cls._validate_prices(config, errors)
        cls._validate_storage(config, errors)
        cls._validate_tokens(config, errors)
        cls._validate_energy(config, errors)

        if errors:
            raise TrainingConfigValidationError(
                "TrainingConfig validation failed: " + "; ".join(errors)
            )

    @staticmethod
    def _validate_hours(config, errors):
        if config.training_hours <= 0:
            errors.append("training_hours must be greater than 0")

    @staticmethod
    def _validate_prices(config, errors):
        if config.gpu_hour_price < 0:
            errors.append("gpu_hour_price cannot be negative")
        if config.cpu_hour_price < 0:
            errors.append("cpu_hour_price cannot be negative")

    @staticmethod
    def _validate_storage(config, errors):
        if config.dataset_size_gb < 0:
            errors.append("dataset_size_gb cannot be negative")
        if config.storage_price_per_gb < 0:
            errors.append("storage_price_per_gb cannot be negative")

    @staticmethod
    def _validate_tokens(config, errors):
        if config.tokens_used < 0:
            errors.append("tokens_used cannot be negative")

        if config.tokens_used > 0 and config.token_price_per_million <= 0:
            errors.append(
                "token_price_per_million must be > 0 when tokens_used > 0"
            )

    @staticmethod
    def _validate_energy(config, errors):
        if not config.energy_source:
            errors.append("energy_source cannot be empty")
