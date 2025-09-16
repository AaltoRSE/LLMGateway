"""
This module provides Usage repository functionality
It needs to provide ways to obtain the current balance and to
add new usage entries. For convenience, balance is commonly handled on a "per month"
basis, so requesting a balance for a specific dattime will always refer to that
datetimes month.

"""

from typing import List
from datetime import datetime
from app.schemas.usage_schema import APIRequest, Usage, Balance, RequestSource


class UsageRepository:

    async def log_usage(self, usage: APIRequest, source: RequestSource) -> None:
        """
        Add the given request to the database and update the balance.
        At least one of user_id and key have to be non None.
        Parameters
        ----------
        usage : APIRequest
            Information about the APIRequest
        user_id: str
            The id of the calling user, can be null if only associated with a key
        key: str
            The access key associated with this request (if any)
        Returns
        -------
        Balance
            The current balance for the given user after the request
        """
        raise NotImplementedError

    async def get_usage_for_user_in_range(
        self, user_id: str, from_time: datetime, to_time: datetime
    ) -> Usage:
        """
        Get usage data for a user within a specific time range.

        Parameters
        ----------
        user_id : str
            The ID of the user to retrieve usage data for.
        from_time : datetime
            The start of the time range.
        to_time : datetime
            The end of the time range.

        Returns
        -------
        Usage
            An overview of the user's usage within the specified time range.
        """
        raise NotImplementedError

    async def get_usage_details_for_user(
        self,
        user_id: str,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> List[APIRequest]:
        """
        Get detailed usage data for a user.

        Parameters
        ----------
        user_id : str
            The ID of the user to retrieve detailed usage data for.
        from_time : datetime
            The start of the time range.
        to_time : datetime
            The end of the time range.
        Returns
        -------
        List[APIRequest]
            A list of detailed usage data for the specified user.
        """
        raise NotImplementedError

    async def get_usage_for_key_in_range(
        self, key: str, from_time: datetime, to_time: datetime
    ) -> Usage:
        """
        Get usage data for a key within a specific time range.

        Parameters
        ----------
        key : str
            The key to retrieve usage data for.
        from_time : datetime
            The start of the time range.
        to_time : datetime
            The end of the time range.

        Returns
        -------
        Usage
            An overview of the keys's usage within the specified time range.
        """
        raise NotImplementedError

    async def get_usage_details_for_key(
        self,
        key: str,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> List[APIRequest]:
        """
        Get detailed usage data for a key.

        Parameters
        ----------
        key : str
            The key to retrieve detailed usage data for.
        from_time : datetime
            The start of the time range.
        to_time : datetime
            The end of the time range.
        Returns
        -------
        List[APIRequest]
            A list of detailed usage data for the specified key.
        """
        raise NotImplementedError
