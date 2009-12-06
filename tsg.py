#!/usr/bin/env python

from pysqlite2 import dbapi2 as sqlite
from git import *
import re
import sys
import os

# Tables and columns that can contain SVN revision IDs
tables = {
	'ticket_change': ['newvalue'],
	'ticket': ['summary', 'description'],
	'wiki': ['text']
}

# Fill SVN revision -> GIT commit hash dictionary
def filldict(path):
	gitsvnrn = re.compile('git-svn-id: [^@]+@([0-9]+)')
	svndict = {}
	repo = Repo(path)
	for commit in repo.commits(max_count = repo.commit_count()):
		match = gitsvnrn.search(commit.message)
		revnum = 'r' + match.group(1)
		svndict[revnum] = commit.id
	return svndict

# Replace all SVN revisions with GIT commit hashes
def git2svn(text):
	outtext = text
	for match in revnum.finditer(text):
		rev = match.group(1)
		sha = svndict.get(rev, rev)
		outtext = outtext.replace(rev, sha)
	return outtext	

try:
	svndict = filldict(sys.argv[1])
	if not os.path.exists(sys.argv[2]):
		raise
	connection = sqlite.connect(sys.argv[2])
	cursor = connection.cursor()
	cursor.execute('SELECT * FROM system') # Test connection
except:
	print 'Usage:', sys.argv[0], '<git path> <trac db path>'
	sys.exit(1)

revnum = re.compile('(r[0-9]+)')

for table, columns in tables.iteritems():
	for column in columns:
		print '[' + table + '/' + column + ']'
		cursor.execute('SELECT ROWID, ' + column + ' FROM ' + table +
			' WHERE ' + column + ' LIKE "% r%"')
		cache = {}
		for row in cursor:
			txt = row[1]
			gitxt = git2svn(row[1])
			if gitxt != txt:
				cache[row[0]] = gitxt
				print 'Change @ ROWID', row[0]
		for rowid, value in cache.iteritems():
			cursor.execute('UPDATE ' + table + ' SET ' + column +
				' = ? WHERE ROWID = ?', (value, rowid))

cursor.close()
connection.commit()
connection.close()
