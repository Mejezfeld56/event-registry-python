from .Base import QueryParamsBase
import six


class QueryItems:
    _AND = "$and"
    _OR = "$or"
    _Undef = None

    def __init__(self, oper, items):
        self._oper = oper
        self._items = items;

    @staticmethod
    def AND(items):
        return QueryItems(QueryItems._AND, items)

    @staticmethod
    def OR(items):
        return QueryItems(QueryItems._OR, items)

    def getOper(self):
        return self._oper

    def getItems(self):
        return self._items



class _QueryCore(object):
    def __init__(self):
        self._queryObj = {}


    def getQuery(self):
        return self._queryObj


    def setQueryParam(self, paramName, val):
        self._queryObj[paramName] = val


    def _setValIfNotDefault(self, propName, value, defVal):
        if value != defVal:
            self._queryObj[propName] = value



class BaseQuery(_QueryCore):
    def __init__(self,
                 keyword = None,
                 conceptUri = None,
                 sourceUri = None,
                 locationUri = None,
                 categoryUri = None,
                 lang = None,
                 dateStart = None,
                 dateEnd = None,
                 dateMentionStart = None,
                 dateMentionEnd = None,
                 categoryIncludeSub = True,
                 minMaxArticlesInEvent = None):
        """
        @param keyword: keyword(s) to query. Either None, string or QueryItems
        @param conceptUri: concept(s) to query. Either None, string or QueryItems
        @param sourceUri: source(s) to query. Either None, string or QueryItems
        @param locationUri: location(s) to query. Either None, string or QueryItems
        @param categoryUri: categories to query. Either None, string or QueryItems
        @param lang: language(s) to query. Either None, string or QueryItems
        @param dateStart: starting date. Either None, string or date or datetime
        @param dateEnd: ending date. Either None, string or date or datetime
        @param dateMentionStart: search by mentioned dates - use this as the starting date. Either None, string or date or datetime
        @param dateMentionEnd: search by mentioned dates - use this as the ending date. Either None, string or date or datetime
        @param categoryIncludeSub: should we include the subcategories of the searched categories?
        @param minMaxArticlesInEvent: a tuple containing the minimum and maximum number of articles that should be in the resulting events. Parameter relevant only if querying events
        """
        super(BaseQuery, self).__init__()

        self._setQueryArrVal("keyword", keyword)
        self._setQueryArrVal("conceptUri", conceptUri)
        self._setQueryArrVal("sourceUri", sourceUri)
        self._setQueryArrVal("locationUri", locationUri)
        self._setQueryArrVal("categoryUri", categoryUri)
        self._setQueryArrVal("lang", lang)

        # starting date of the published articles (e.g. 2014-05-02)
        if dateStart != None:
            self._queryObj["dateStart"] = QueryParamsBase.encodeDate(dateStart)
        # ending date of the published articles (e.g. 2014-05-02)
        if dateEnd != None:
            self._queryObj["dateEnd"] = QueryParamsBase.encodeDate(dateEnd)

        # first valid mentioned date detected in articles (e.g. 2014-05-02)
        if dateMentionStart != None:
            self._queryObj["dateMentionStart"] = QueryParamsBase.encodeDate(dateMentionStart)
        # last valid mentioned date detected in articles (e.g. 2014-05-02)
        if dateMentionEnd != None:
            self._queryObj["dateMentionEnd"] = QueryParamsBase.encodeDate(dateMentionEnd)
        if minMaxArticlesInEvent != None:
            assert isinstance(minMaxArticlesInEvent, tuple), "minMaxArticlesInEvent parameter should either be None or a tuple with two integer values"
            self._queryObj["minArticlesInEvent"] = minMaxArticlesInEvent[0]
            self._queryObj["maxArticlesInEvent"] = minMaxArticlesInEvent[1]


    def _setQueryArrVal(self, propName, value):
        # by default we have None - so don't do anything
        if value is None:
            return
        # if we have an instance of QueryItems then apply it
        if isinstance(value, QueryItems):
            self._queryObj[propName] = { value.getOper(): value.getItems() }

        # if we have a string value, just use it
        elif isinstance(value, six.string_types):
            self._queryObj[propName] = value
        # there should be no other valid types
        else:
            assert False, "Parameter '%s' was of unsupported type" % (propName)



class CombinedQuery(_QueryCore):
    def __init__(self):
        super(CombinedQuery, self).__init__()


    @staticmethod
    def AND(queryArr):
        """
        create a combined query with multiple items on which to perform an AND operation
        @param queryArr: a list of items on which to perform an AND operation. Items can be either a CombinedQuery or BaseQuery instances.
        """
        assert isinstance(queryArr, list), "provided argument as not a list"
        assert len(queryArr) > 0, "queryArr had an empty list"
        q = CombinedQuery()
        q.setQueryParam("$and", [])
        for item in queryArr:
            assert isinstance(item, (CombinedQuery, BaseQuery)), "item in the list was not a CombinedQuery or BaseQuery instance"
            q.getQuery()["$and"].append(item.getQuery())
        return q


    @staticmethod
    def OR(queryArr):
        """
        create a combined query with multiple items on which to perform an OR operation
        @param queryArr: a list of items on which to perform an OR operation. Items can be either a CombinedQuery or BaseQuery instances.
        """
        assert isinstance(queryArr, list), "provided argument as not a list"
        assert len(queryArr) > 0, "queryArr had an empty list"
        q = CombinedQuery()
        q.setQueryParam("$or", [])
        for item in queryArr:
            assert isinstance(item, (CombinedQuery, BaseQuery)), "item in the list was not a CombinedQuery or BaseQuery instance"
            q.getQuery()["$or"].append(item.getQuery())
        return q



class ComplexArticleQuery(_QueryCore):
    def __init__(self,
                 includeQuery,
                 excludeQuery = None,
                 isDuplicateFilter = "keepAll",
                 hasDuplicateFilter = "keepAll",
                 eventFilter = "keepAll"):
        """
        create an article query using a complex query
        @param includeQuery: an instance of CombinedQuery or BaseQuery to use to find articles that match the conditions
        @param excludeQuery: an instance of CombinedQuery or BaseQuery (or None) to find articles to exclude from the articles matched with the includeQuery
        @param isDuplicateFilter: some articles can be duplicates of other articles. What should be done with them. Possible values are:
                "skipDuplicates" (skip the resulting articles that are duplicates of other articles)
                "keepOnlyDuplicates" (return only the duplicate articles)
                "keepAll" (no filtering, default)
        @param hasDuplicateFilter: some articles are later copied by others. What should be done with such articles. Possible values are:
                "skipHasDuplicates" (skip the resulting articles that have been later copied by others)
                "keepOnlyHasDuplicates" (return only the articles that have been later copied by others)
                "keepAll" (no filtering, default)
        @param eventFilter: some articles describe a known event and some don't. This filter allows you to filter the resulting articles based on this criteria.
                Possible values are:
                "skipArticlesWithoutEvent" (skip articles that are not describing any known event in ER)
                "keepOnlyArticlesWithoutEvent" (return only the articles that are not describing any known event in ER)
                "keepAll" (no filtering, default)
        """
        super(ComplexArticleQuery, self).__init__()

        assert isinstance(includeQuery, (CombinedQuery, BaseQuery)), "includeQuery parameter was not a CombinedQuery or BaseQuery instance"
        self._queryObj["include"] = includeQuery.getQuery()
        if excludeQuery != None:
            assert isinstance(excludeQuery, (CombinedQuery, BaseQuery)), "excludeQuery parameter was not a CombinedQuery or BaseQuery instance"
            self._queryObj["exclude"] = excludeQuery.getQuery()

        self._setValIfNotDefault("isDuplicateFilter", isDuplicateFilter, "keepAll")
        self._setValIfNotDefault("hasDuplicateFilter", hasDuplicateFilter, "keepAll")
        self._setValIfNotDefault("eventFilter", eventFilter, "keepAll")



class ComplexEventQuery(_QueryCore):
    def __init__(self,
                 includeQuery,
                 excludeQuery = None):
        """
        create an event query suing a complex query
        @param includeQuery: an instance of CombinedQuery or BaseQuery to use to find events that match the conditions
        @param excludeQuery: an instance of CombinedQuery or BaseQuery (or None) to find events to exclude from the events matched with the includeQuery
        """
        super(ComplexEventQuery, self).__init__()

        assert isinstance(includeQuery, (CombinedQuery, BaseQuery)), "includeQuery parameter was not a CombinedQuery or BaseQuery instance"
        self._queryObj["include"] = includeQuery.getQuery()
        if excludeQuery != None:
            assert isinstance(excludeQuery, (CombinedQuery, BaseQuery)), "excludeQuery parameter was not a CombinedQuery or BaseQuery instance"
            self._queryObj["exclude"] = excludeQuery.getQuery()
