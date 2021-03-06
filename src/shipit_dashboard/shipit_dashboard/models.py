# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import datetime
import pickle
import sqlalchemy as sa

from releng_common.db import db


# M2M link between analysis & bug
bugs = db.Table(
    'analysis_bugs',
    sa.Column('analysis_id', sa.Integer, sa.ForeignKey('shipit_bug_analysis.id')),  # noqa
    sa.Column('bug_id', sa.Integer, sa.ForeignKey('shipit_bug_result.id'))
)


class BugAnalysis(db.Model):
    """
    A template to build some cached analysis
    by listing several bugs from Bugzilla, with
    their analysus
    """
    __tablename__ = 'shipit_bug_analysis'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80))
    parameters = sa.Column(sa.Text())
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    bugs = db.relationship('BugResult', secondary=bugs, backref=db.backref('analysis', lazy='dynamic'))  # noqa

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'AnalysisTemplate {}'.format(self.name)


class BugResult(db.Model):
    """
    The cached result of an analysis run
    """
    __tablename__ = 'shipit_bug_result'

    id = sa.Column(sa.Integer, primary_key=True)
    bugzilla_id = sa.Column(sa.Integer, unique=True)
    payload = sa.Column(sa.Binary())
    payload_hash = sa.Column(sa.String(40))

    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, bugzilla_id):
        self.bugzilla_id = bugzilla_id

    def __repr__(self):
        return 'BugResult {}'.format(self.bugzilla_id)

    @property
    def payload_data(self):
        if not self.payload:
            return None
        return pickle.loads(self.payload)

    def delete(self):
        """
        Delete bug and its dependencies
        """
        # Delete links, avoid StaleDataError
        db.engine.execute(sa.text('delete from analysis_bugs where bug_id = :bug_id'), bug_id=self.id)  # noqa

        # Delete the bug
        db.session.delete(self)
        db.session.commit()


class Contributor(db.Model):
    """
    An active Mozilla contributor
    """
    __tablename__ = 'shipit_contributor'
    id = sa.Column(sa.Integer, primary_key=True)
    bugzilla_id = sa.Column(sa.Integer, unique=True)
    name = sa.Column(sa.String(250))
    email = sa.Column(sa.String(250))
    avatar_url = sa.Column(sa.String(250))


class BugContributor(db.Model):
    """
    M2M link between contributor & bug
    """
    __tablename__ = 'shipit_contributor_bugs'
    __table_args__ = (
        sa.UniqueConstraint('contributor_id', 'bug_id', name='uniq_contrib_bug'),  # noqa
    )

    id = sa.Column(sa.Integer, primary_key=True)
    contributor_id = sa.Column(sa.Integer, sa.ForeignKey('shipit_contributor.id'))  # noqa
    bug_id = sa.Column(sa.Integer, sa.ForeignKey('shipit_bug_result.id'))
    roles = sa.Column(sa.String(250))

    bug = db.relationship(BugResult, backref="contributors")
    contributor = db.relationship(Contributor, backref="bugs")
