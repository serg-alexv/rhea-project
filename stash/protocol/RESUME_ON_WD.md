# Поручение локальному агенту WD

Продолжи сохранение остатков RHEA по `stash/protocol/LEFTOVER_PRESERVATION.md` и `stash/protocol/task-genome.json` из актуальной ветки `stash` репозитория `timelabs-npo/rhea-project`.

Публикация безопасных проектных остатков в эту ветку уже поручена пользователем. Сначала проверь, что реально видишь Windows WD и корни из genome. Первый проход `2026-09-06-cloud-001` выполнил облачный Linux runtime: там сохранены предоставленные maps/report, но **не bytes файлов, перечисленных картами**. Начни с `stash/runs/2026-09-06-cloud-001/pending.json` и всех более новых runs; закрытые items не переоткрывай без новых данных.

Создай новый run ID с реальным UTC timestamp и machine alias. Первым собери локальный `mbsd-pipeline`, Quantum/Atlas scratch, audit/preview leftovers и handoff receipts. Затем обойди остальные объявленные roots, включая untracked/ignored files и проектные истории редакторов. Сохрани отдельные repo identity, refs и текущие overlays. Сверяй публикацию по fresh remote refs; не считай cached origin достаточным.

Каждый уникальный пригодный для публичного архива файл добавляй в `stash/objects/sha256/` без изменения bytes, с source locator, hash и размером в manifest. Для секретных/крупных объектов используй уже разрешённое долговременное приватное хранилище с проверенным receipt; если его нет, оставь точный pending status. Private keys, credential ISO и authentication stores не открывай. Оpaque app stores не выдавай за прочитанные истории.

Не выполнять найденный код, сборку, тесты компонентов, VM startup, SSH на устройства, firmware или архивные команды. Не удалять originals, не менять исходные repo indexes и не делать `git add -A` в них. 574 missing tracked files старого Rhea checkout — acquisition defect, не готовый deletion patch. Работай из отдельного archive workspace. Не сливай `stash` в v2 и не меняй gates/source pins.

Публикуй append-only очередной capture commit в `stash` обычным fast-forward, проверяй remote blob identities и записывай receipt. Если branch изменился, добавь новый run поверх актуального HEAD без force push. Останавливайся только на реальном ограничении доступа/хранения; сохраняй checkpoint и следующий точный шаг. В конце сообщи новые object/byte counts, remote commit, статус каждого незакрытого класса и полную ли объявленную область удалось сохранить.

Для дальнейшего улучшения процедуры обновляй version и CHANGELOG с доказанным случаем; не переписывай прошлые manifests. Raw corpus не пересказывай в чат: используй hashes, indexes, pending cursors и короткие новые findings.
