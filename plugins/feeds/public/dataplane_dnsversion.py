"""
    Feed DNS Version IPs with ASN
"""
from datetime import timedelta
import logging
from typing import ClassVar

import pandas as pd
from core.schemas.observables import ipv4, asn
from core.schemas import task
from core import taskmanager


class DataplaneDNSVersion(task.FeedTask):
    """
    Feed DNS Version IPs with ASN
    """

    _SOURCE: ClassVar["str"] = "https://dataplane.org/dnsversion.txt"
    _defaults = {
        "frequency": timedelta(hours=12),
        "name": "DataplaneDNSVersion",
        "description": "Feed DNS Version IPs with ASN",
    }
    _NAMES = ["ASN", "ASname", "ipaddr", "lastseen", "category"]

    def run(self):
        response = self._make_request(self._SOURCE, sort=False)
        if response:
            lines = response.content.decode("utf-8").split("\n")[66:-5]

            df = pd.DataFrame([l.split("|") for l in lines], columns=self._NAMES)

            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            df.ffill(inplace=True)
            df["lastseen"] = pd.to_datetime(df["lastseen"])
            df = self._filter_observables_by_time(df, "lastseen")

            for _, row in df.iterrows():
                self.analyze(row)

    def analyze(self, item):
        if not item["ipaddr"]:
            return
        
        context_ip = {
            "source": self.name,
        }
        
        ip_obs = ipv4.IPv4(value=item["ipaddr"]).save()
        category = item["category"].lower()
        tags = ["dataplane", "dnsversion"]
        if category:
            tags.append(category)
        logging.debug(f"Adding context {context_ip} to {ip_obs}")
        ip_obs.add_context("dataplane dns version", context_ip)
        ip_obs.tag(tags)
        asn_obs = asn.ASN(value=item["ASN"]).save()
        context_asn = {
            "source": self.name,
            "name": item["ASname"],
            "last_seen": item["lastseen"],
        }
        asn_obs.add_context(self.name, context_asn)
        asn_obs.tag(tags)

        asn_obs.link_to(ip_obs, "ASN_IP", self.name)


taskmanager.TaskManager.register_task(DataplaneDNSVersion)
