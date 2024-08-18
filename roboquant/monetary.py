from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar


class Currency(str):
    """Currency class represents a monetary currency and is s subclass of `str`"""

    def __rmatmul__(self, other: float | int):
        assert isinstance(other, (float, int))
        return Amount(self, other)


# Commonly used currencies
USD = Currency("USD")
EUR = Currency("EUR")
JPY = Currency("JPY")
GBP = Currency("GBP")
CHF = Currency("CHF")
INR = Currency("INR")
AUD = Currency("AUD")
CAD = Currency("CAD")
NZD = Currency("NZD")
CMY = Currency("CMY")
HKD = Currency("HKD")
BTC = Currency("BTC")
ETH = Currency("ETH")


class CurrencyConverter(ABC):
    """Abstract base class for currency converters"""

    @abstractmethod
    def convert(self, amount: "Amount", to_currency: Currency, time: datetime) -> float:
        """Convert the monetary amount into another currency at the provided time."""
        ...


class NoConversion(CurrencyConverter):
    """The default currency converter that doesn't convert between currencies"""

    def convert(self, amount: "Amount", to_currency: Currency, time: datetime) -> float:
        raise NotImplementedError("The default NoConversion doesn't support any conversions")


class StaticConversion(CurrencyConverter):
    """Currency converter that uses static rates to convert between different currencies.
    This converter doesn't take time into consideration.
    """

    def __init__(self, base_currency: Currency, rates: dict[Currency, float]):
        super().__init__()
        self.base_currency = base_currency
        self.rates = rates
        self.rates[base_currency] = 1.0

    def convert(self, amount: "Amount", to_currency: Currency, time: datetime) -> float:
        return amount.value * self.rates[amount.currency] / self.rates[to_currency]


class One2OneConversion(CurrencyConverter):
    """Currency converter that always converts 1 to 1 between currencies.
    So for example, 1 USD equals 1 EUR equals 1 GPB"""

    def convert(self, amount: "Amount", to_currency: str, time: datetime) -> float:
        return amount.value


@dataclass(frozen=True, slots=True)
class Amount:
    """A monetary value denoted in a single currency. Amounts are immutable"""

    currency: Currency
    value: float
    __converter: ClassVar[CurrencyConverter] = NoConversion()

    @staticmethod
    def register_converter(converter: CurrencyConverter):
        """Register a new currency converter to handle conversions between different currencies"""
        Amount.__converter = converter

    def items(self):
        return [(self.currency, self.value)]

    def amounts(self):
        return [self]

    def __add__(self, other: "Amount") -> "Wallet":
        """Add another amount to this amount.
        This will always return a wallet, even if both amounts have the same currency.
        """
        return Wallet(self, other)

    def convert(self, currency: Currency, time: datetime) -> float:
        """Convert this amount to another currency and return that value.
        If a conversion is required, it will invoke the registered `Amount.converter`.
        """
        if currency == self.currency:
            return self.value
        if self.value == 0.0:
            return 0.0

        return Amount.__converter.convert(self, currency, time)

    def __repr__(self) -> str:
        return f"{self.value:,.2f}@{self.currency}"


class Wallet(defaultdict[Currency, float]):
    """A wallet holds monetary values of different currencies"""

    def __init__(self, *amounts: Amount):
        super().__init__(float)
        for amount in amounts:
            self[amount.currency] += amount.value

    def amounts(self):
        """Return the amounts contained in this wallet"""
        return [Amount(k, v) for k, v in self.items()]

    def __iadd__(self, other: "Amount | Wallet"):
        for k, v in other.items():
            self[k] += v
        return self

    def __isub__(self, other: "Amount | Wallet"):
        for k, v in other.items():
            self[k] -= v
        return self

    def __add__(self, other: "Amount | Wallet"):
        result = self.deepcopy()
        for k, v in other.items():
            result[k] += v
        return result

    def __sub__(self, other: "Amount | Wallet"):
        result = self.deepcopy()
        for k, v in other.items():
            result[k] -= v
        return result

    def deepcopy(self) -> "Wallet":
        result = Wallet()
        result.update(self)
        return result

    def convert(self, currency: Currency, time: datetime) -> float:
        """convert all the amounts hold in this wallet to a single currency and return the value"""
        return sum(amount.convert(currency, time) for amount in self.amounts())

    def __repr__(self) -> str:
        return " + ".join([f"{a}" for a in self.amounts()])
