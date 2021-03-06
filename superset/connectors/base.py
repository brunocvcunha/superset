import json

from sqlalchemy import Column, Integer, String, Text, Boolean

from superset import utils
from superset.models.helpers import AuditMixinNullable, ImportMixin


class BaseDatasource(AuditMixinNullable, ImportMixin):

    """A common interface to objects that are queryable (tables and datasources)"""

    __tablename__ = None  # {connector_name}_datasource

    # Used to do code highlighting when displaying the query in the UI
    query_language = None

    @property
    def column_names(self):
        return sorted([c.column_name for c in self.columns])

    @property
    def main_dttm_col(self):
        return "timestamp"

    @property
    def groupby_column_names(self):
        return sorted([c.column_name for c in self.columns if c.groupby])

    @property
    def filterable_column_names(self):
        return sorted([c.column_name for c in self.columns if c.filterable])

    @property
    def dttm_cols(self):
        return []

    @property
    def url(self):
        return '/{}/edit/{}'.format(self.baselink, self.id)

    @property
    def explore_url(self):
        if self.default_endpoint:
            return self.default_endpoint
        else:
            return "/superset/explore/{obj.type}/{obj.id}/".format(obj=self)

    @property
    def column_formats(self):
        return {
            m.metric_name: m.d3format
            for m in self.metrics
            if m.d3format
        }

    @property
    def data(self):
        """Data representation of the datasource sent to the frontend"""
        order_by_choices = []
        for s in sorted(self.column_names):
            order_by_choices.append((json.dumps([s, True]), s + ' [asc]'))
            order_by_choices.append((json.dumps([s, False]), s + ' [desc]'))

        d = {
            'all_cols': utils.choicify(self.column_names),
            'column_formats': self.column_formats,
            'edit_url': self.url,
            'filter_select': self.filter_select_enabled,
            'filterable_cols': utils.choicify(self.filterable_column_names),
            'gb_cols': utils.choicify(self.groupby_column_names),
            'id': self.id,
            'metrics_combo': self.metrics_combo,
            'name': self.name,
            'order_by_choices': order_by_choices,
            'type': self.type,
        }

        # TODO move this block to SqlaTable.data
        if self.type == 'table':
            grains = self.database.grains() or []
            if grains:
                grains = [(g.name, g.name) for g in grains]
            d['granularity_sqla'] = utils.choicify(self.dttm_cols)
            d['time_grain_sqla'] = grains
        return d


class BaseColumn(AuditMixinNullable, ImportMixin):
    """Interface for column"""

    __tablename__ = None  # {connector_name}_column

    id = Column(Integer, primary_key=True)
    column_name = Column(String(255))
    verbose_name = Column(String(1024))
    is_active = Column(Boolean, default=True)
    type = Column(String(32))
    groupby = Column(Boolean, default=False)
    count_distinct = Column(Boolean, default=False)
    sum = Column(Boolean, default=False)
    avg = Column(Boolean, default=False)
    max = Column(Boolean, default=False)
    min = Column(Boolean, default=False)
    filterable = Column(Boolean, default=False)
    description = Column(Text)

    # [optional] Set this to support import/export functionality
    export_fields = []

    def __repr__(self):
        return self.column_name

    num_types = ('DOUBLE', 'FLOAT', 'INT', 'BIGINT', 'LONG', 'REAL', 'NUMERIC')
    date_types = ('DATE', 'TIME', 'DATETIME')
    str_types = ('VARCHAR', 'STRING', 'CHAR')

    @property
    def is_num(self):
        return any([t in self.type.upper() for t in self.num_types])

    @property
    def is_time(self):
        return any([t in self.type.upper() for t in self.date_types])

    @property
    def is_string(self):
        return any([t in self.type.upper() for t in self.str_types])


class BaseMetric(AuditMixinNullable, ImportMixin):

    """Interface for Metrics"""

    __tablename__ = None  # {connector_name}_metric

    id = Column(Integer, primary_key=True)
    metric_name = Column(String(512))
    verbose_name = Column(String(1024))
    metric_type = Column(String(32))
    description = Column(Text)
    is_restricted = Column(Boolean, default=False, nullable=True)
    d3format = Column(String(128))

    """
    The interface should also declare a datasource relationship pointing
    to a derivative of BaseDatasource, along with a FK

    datasource_name = Column(
        String(255),
        ForeignKey('datasources.datasource_name'))
    datasource = relationship(
        # needs to be altered to point to {Connector}Datasource
        'BaseDatasource',
        backref=backref('metrics', cascade='all, delete-orphan'),
        enable_typechecks=False)
    """
    @property
    def perm(self):
        raise NotImplementedError()
