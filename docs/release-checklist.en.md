# Release checklist

[한국어](release-checklist.md) | English · [Home](../README.en.md) · [Changelog](../CHANGELOG.en.md) · [Development guide](development.en.md)

Version `0.99.1` is an experimental preview; stable `1.0` is planned after validation and fixes. These are preparation requirements, not completed results. Documentation work or a test ZIP alone does not create a version bump, tag, or GitHub Release.

## Version and documentation

- [ ] Confirm the release version in `navermap_qgis_bridge/metadata.txt`.
- [ ] Record changes, update instructions, verification scope, and remaining limitations in the changelog.
- [ ] Check that the README, setup, usage, troubleshooting, and installation README describe the same behavior in both languages.
- [ ] Distinguish ZIP labels from official version numbers.

## Environment verification

- [ ] Run Python core and mocked-SDK web checks and record the results.
- [ ] Check relevant scenarios on QGIS 3.34 LTR or later, including the external browser.
- [ ] Check the embedded viewer and coordinate/route/history functionality on QGIS 4.x.
- [ ] Verify changes to authentication, search, routes, history, language, and shared layouts in both environments.
- [ ] Record the environment and actual results in the [installation checklist](install-test-checklist.en.md). Separate unperformed checks from passes.

## Security and package

- [ ] Review `git diff` and `git status` for real keys, `settings.json`, and personal files.
- [ ] Confirm GPL-2.0-or-later compatibility and record external sources/licenses.
- [ ] Build the ZIP and verify its only top-level folder is `navermap_qgis_bridge/`.
- [ ] Check Python modules, every manifest web asset, LICENSE, and user documentation.
- [ ] Exclude keys, local settings, caches, development dependencies, and user history data.
- [ ] Check relative README/documentation links inside the ZIP, validate CRC, and record SHA256.
- [ ] Test fresh installation, update, and restart in a separate QGIS profile.

## Publish

Confirm that version, commit, ZIP, and release notes agree before proceeding with an authorized release. Attach the QGIS installation ZIP separately from GitHub's automatic source archives. Download the published ZIP and recheck its structure, hash, and documentation links.

## Submit the 0.99.1 preview to the QGIS repository

1. Sign in to the [QGIS plugin repository](https://plugins.qgis.org/) with an account allowed to upload the plugin.
2. Check ownership and existing versions. If `0.99.1` is already registered, it cannot be overwritten with the same version; choose the next version instead.
3. Use [Upload a plugin](https://plugins.qgis.org/plugins/add/) and select `navermap_qgis_bridge-0.99.zip`. Keep the existing module name `navermap_qgis_bridge` and plugin title.
4. Check imported version 0.99.1, minimum QGIS 3.34, maximum 4.99, Experimental enabled, public source/homepage/issue links, and English description.
5. Confirm the submission result and record its review/approval status. Submission alone does not establish publication or approval.

Check minimal documentation, an English description, public source/homepage/issue links, a GPL-compatible license, and package structure against the [official publishing requirements](https://plugins.qgis.org/docs/publish). The ZIP must not exceed 25MB or include actual keys or executable binaries. Also check version uniqueness and the single plugin folder required by the [release documentation](https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/releasing.html).

Ownership, existing registered versions, and review status must be checked in the authenticated repository interface. Do not record local ZIP validation as a completed repository upload or approval.
