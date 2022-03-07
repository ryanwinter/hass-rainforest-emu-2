import math
from xml.etree import ElementTree

# Base class for a response entity. All individual response
# objects inherit from this.
class Entity:
    def __init__(self, tree):
        self._tree = tree

        # These tags are common to all responses
        self.device_mac = self.find_text('DeviceMacId')

        self._parse()

    # def __repr__(self):
    #     return ElementTree.tostring(self._tree).decode('ASCII')

    # Hook for subclasses to override to provide special parsing
    # for computing their parameters.
    def _parse(self):
        return

    def find_text(self, tag):
        node = self._tree.find(tag)
        if node is None:
            return None
        return node.text

    def find_hex(self, text):
        return int(self.find_text(text) or "0x00", 16)

    # The root element associated with this class
    @classmethod
    def tag_name(cls):
        return cls.__name__

    # Map the tag name to the type of subclass
    @classmethod
    def tag_to_class(cls, tag):
        for klass in cls.__subclasses__():
            if klass.tag_name() == tag:
                return klass
        return None

#####################################
#       Raven Notifications         #
#####################################
class ConnectionStatus(Entity):
    def _parse(self):
        self.meter_mac = self.find_text('MeterMacId')
        self.status = self.find_text("Status")
        self.description = self.find_text("Description")
        self.status_code = self.find_text("StatusCode")         # 0x00 to 0xFF
        self.extended_pan_id = self.find_text("ExtPanId")
        self.channel = self.find_text("Channel")                # 11 to 26
        self.short_address = self.find_text("ShortAddr")        # 0x0000 to 0xFFFF
        self.link_strength = self.find_text("LinkStrength")     # 0x00 to 0x64

class DeviceInfo(Entity):
    def _parse(self):
        self.install_code = self.find_text("InstallCode")
        self.link_key = self.find_text("LinkKey")
        self.fw_version = self.find_text("FWVersion")
        self.hw_version = self.find_text("HWVersion")
        self.fw_image_type = self.find_text("ImageType")
        self.manufacturer = self.find_text("Manufacturer")
        self.model_id = self.find_text("ModelId")
        self.date_code = self.find_text("DateCode")

class ScheduleInfo(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.event = self.find_text("Event")
        self.frequency = self.find_text("Frequency")
        self.enabled = self.find_text("Enabled")

# TODO: There can be more than one MeterMacId
class MeterList(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")

#####################################
#       Meter Notifications         #
#####################################
class MeterInfo(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.meter_type = self.find_text("MeterType")
        self.nickname = self.find_text("NickName")
        self.account = self.find_text("Account")
        self.auth = self.find_text("Auth")
        self.host = self.find_text("Host")
        self.enabled = self.find_text("Enabled")

class NetworkInfo(Entity):
    def _parse(self):
        self.coordinator_mac = self.find_text("CoordMacId")
        self.status = self.find_text("Status")
        self.description = self.find_text("Description")
        self.status_code = self.find_text("StatusCode")
        self.extended_pan_id = self.find_text("ExtPanId")
        self.channel = self.find_text("Channel")
        self.short_address = self.find_text("ShortAddr")
        self.link_strength = self.find_text("LinkStrength")

#####################################
#        Time Notifications         #
#####################################

# TODO: Convert from Rainforest epoch
class TimeCluster(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.utc_time = self.find_text("UTCTime")
        self.local_time = self.find_text("LocalTime")

#####################################
#      Message Notifications        #
#####################################
class MessageCluster(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.timestamp = self.find_hex("TimeStamp")
        self.id = self.find_text("Id")
        self.text = self.find_text("Text")
        self.confirmation_required = self.find_text("ConfirmationRequired")
        self.confirmed = self.find_text("Confirmed")
        self.queue = self.find_text("Queue")

#####################################
#        Price Notifications        #
#####################################
class PriceCluster(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.timestamp = self.find_hex("TimeStamp")
        self.price = self.find_hex("Price")
        self.currency = self.find_text("Currency")      # ISO-4217
        self.trailing_digits = self.find_hex("TrailingDigits")
        self.tier = self.find_text("Tier")
        self.tier_label = self.find_text("TierLabel")
        self.rate_label = self.find_text("RateLabel")

        if (self.price != 0xffffffff):
            self.price_dollars = self.price / math.pow(10, self.trailing_digits)
        else:
            self.price_dollars = None

#####################################
#   Simple Metering Notifications   #
#####################################
class InstantaneousDemand(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.timestamp = self.find_hex("TimeStamp")
        self.demand = self.find_hex("Demand")
        self.multiplier = self.find_hex("Multiplier")
        self.divisor = self.find_hex("Divisor")
        self.digits_right = self.find_hex("DigitsRight")
        self.digits_left = self.find_hex("DigitsLeft")
        self.suppress_leading_zero = self.find_text("SuppressLeadingZero")

        # accept negative numbers
        self.demand = -(self.demand & 0x80000000) | (self.demand & 0x7fffffff)

        # Compute actual reading (protecting from divide-by-zero)
        if self.divisor != 0:
            self.reading = round(self.demand * self.multiplier / float(self.divisor), self.digits_right)
        else:
            self.reading = 0

class CurrentSummationDelivered(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.timestamp = self.find_hex("TimeStamp")
        self.summation_delivered = self.find_hex("SummationDelivered")
        self.summation_received = self.find_hex("SummationReceived")
        self.multiplier = self.find_hex("Multiplier")
        self.divisor = self.find_hex("Divisor")
        self.digits_right = self.find_hex("DigitsRight")
        self.digits_left = self.find_hex("DigitsLeft")
        self.suppress_leading_zero = self.find_text("SuppressLeadingZero")

        # Compute actual reading (protecting from divide-by-zero)
        if self.divisor != 0:
            self.delivered = round(self.summation_delivered * self.multiplier / float(self.divisor), self.digits_right)
            self.received = round(self.summation_received * self.multiplier / float(self.divisor), self.digits_right)
        else:
            self.delivered = 0
            self.received = 0

class CurrentPeriodUsage(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.timestamp = self.find_hex("TimeStamp")
        self.current_usage = self.find_hex("CurrentUsage")
        self.multiplier = self.find_hex("Multiplier")
        self.divisor = self.find_hex("Divisor")
        self.digits_right = self.find_hex("DigitsRight")
        self.digits_left = self.find_hex("DigitsLeft")
        self.suppress_leading_zero = self.find_text("SuppressLeadingZero")
        self.start_date = self.find_hex("StartDate")

        # Compute actual reading (protecting from divide-by-zero)
        if self.divisor != 0:
            self.reading = round(self.current_usage * self.multiplier / float(self.divisor), self.digits_right)
        else:
            self.reading = 0

class LastPeriodUsage(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.last_usage = self.find_hex("LastUsage")
        self.multiplier = self.find_hex("Multiplier")
        self.divisor = self.find_hex("Divisor")
        self.digits_right = self.find_hex("DigitsRight")
        self.digits_left = self.find_hex("DigitsLeft")
        self.suppress_leading_zero = self.find_text("SuppressLeadingZero")
        self.start_date = self.find_hex("StartDate")
        self.end_date = self.find_hex("EndDate")

# TODO: IntervalData may appear more than once
class ProfileData(Entity):
    def _parse(self):
        self.meter_mac = self.find_text("MeterMacId")
        self.end_time = self.find_text("EndTime")
        self.status = self.find_text("Status")
        self.period_interval = self.find_text("ProfileIntervalPeriod")
        self.number_of_periods = self.find_text("NumberOfPeriodsDelivered")
        self.interval_data = self.find_text("IntervalData")
