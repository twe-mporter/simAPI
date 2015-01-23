#!/usr/bin/make
# WARN: gmake syntax
########################################################
# Makefile for simApi extension
#
# useful targets:
#   make clean ----- cleans distutils
#   make pylint ---- source code checks
#   make rpm  ------ produce RPMs
#
########################################################
# variable section

NAME = "simApi"

PYTHON=python
SITELIB = $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

# VERSION file provides one place to update the software version
VERSION := $(shell cat VERSION)

# RPM build parameters
RPMSPECDIR = .
RPMSPEC = $(RPMSPECDIR)/simApi.spec
RPMRELEASE = 1
RPMNVR = "$(NAME)-$(VERSION)-$(RPMRELEASE)"

########################################################

all: clean pylint rpm

pylint:
	find . -name \*.py | xargs pylint 

clean:
	@echo "---------------------------------------------"
	@echo "Cleaning up distutils stuff"
	@echo "---------------------------------------------"
	rm -rf build
	rm -rf dist
	rm -rf MANIFEST
	@echo "---------------------------------------------"
	@echo "Cleaning up rpmbuild stuff"
	@echo "---------------------------------------------"
	rm -rf rpmbuild
	@echo "---------------------------------------------"
	@echo "Cleaning up byte compiled python stuff"
	@echo "---------------------------------------------"
	find . -type f -regex ".*\.py[co]$$" -delete
	@echo "---------------------------------------------"
	@echo "Removing simApi.egg-info"
	@echo "---------------------------------------------"
	rm -rf simApi.egg-info

sdist: clean
	$(PYTHON) setup.py sdist

rpmcommon: sdist
	@mkdir -p rpmbuild
	@cp dist/*.gz rpmbuild/
	@sed -e 's#^Version:.*#Version: $(VERSION)#' -e 's#^Release:.*#Release: $(RPMRELEASE)#' $(RPMSPEC) >rpmbuild/$(NAME).spec

rpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpmbuild" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	--define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.rpm" \
	--define "__python /usr/bin/python" \
	-ba rpmbuild/$(NAME).spec
	@rm -f rpmbuild/$(NAME).spec
	@echo "---------------------------------------------"
	@echo "simApi RPM is built:"
	@echo "    rpmbuild/$(RPMNVR).rpm"
	@echo "---------------------------------------------"
