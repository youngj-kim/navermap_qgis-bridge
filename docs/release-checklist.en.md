# Release checklist

[한국어](release-checklist.md) | English · [Home](../README.en.md) · [Changelog](../CHANGELOG.en.md) · [Development guide](development.en.md)

Version `0.2.0` is currently an experimental development build. These are preparation requirements, not completed results. Documentation work or a test ZIP alone does not create a version bump, tag, or GitHub Release.

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
