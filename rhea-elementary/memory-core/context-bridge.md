# Nexus State Export
Generated UTC: 2026-02-19T22:57:07Z
STATE_HASH = 0cbf2254d803e295a2649d82e066365ee48ea15aec772cf8337e200e67a11a1a
=== PAYLOAD ===
## 1) INVARIANTS
- Every agent writes to inbox/, only LEAD reads and routes
- LEAD updates TODAY_CAPSULE at least every 2 hours
- Every external insight (ChatGPT, web, bridge) goes to GEMS.md immediately
- Every broken thing goes to INCIDENTS.md immediately
- Every decision goes to DECISIONS.md with "why" and "who decided"
- Git push at least every 30 minutes
- Every agent logs API calls to logs/bridge_calls.jsonl

## 2) ROUTES
- inbox: `ops/virtual-office/inbox`
- outbox: `ops/virtual-office/outbox`
- STOP: `ops/virtual-office/STOP`
- agent_id: `--interval`
- agent_id: `B2`
- agent_id: `COWORK`
- agent_id: `LEAD`
- agent_id: `REX`
- agent_id: `gpt`

## 3) LAST KNOWN STATE
### watcher_state.json
- path: `ops/virtual-office/argos/watcher_state.json`
```json
{
  "alerts_sent": 1,
  "boot_count": 9,
  "created_at": "2026-02-17T17:29:56.643951+00:00",
  "last_git_check": "2026-02-19T14:30:32.198534+00:00",
  "last_git_sha": "52482de8fa1c16496ea3e884ced8da125480e94b",
  "last_heartbeat": "",
  "last_inbox_scan": "2026-02-19T14:30:32.198538+00:00",
  "last_mailbox_seq": 4,
  "observations_count": 11
}
```
### snapshots
- path: `ops/virtual-office/snapshots/--interval.json`
```json
{
  "agent": "--interval",
  "last_seq_applied": 0,
  "lease_token": 8,
  "messages_drained": 0,
  "saved_at": "2026-02-19T15:02:36.554546+00:00",
  "state_hash": "1132e5c191440f13"
}
```
- path: `ops/virtual-office/snapshots/B2.json`
```json
{
  "agent": "B2",
  "last_seq_applied": 50,
  "lease_token": 1,
  "messages_drained": 1,
  "saved_at": "2026-02-19T17:51:11.544243+00:00",
  "state_hash": "de001abe9a722099"
}
```
- path: `ops/virtual-office/snapshots/COWORK.json`
```json
{
  "agent": "COWORK",
  "agent_name": "Argos",
  "git_sha": "52482de8",
  "inbox_files": 7,
  "last_seq_applied": 4,
  "lease_token": 12,
  "pending_messages": 1,
  "saved_at": "2026-02-19T14:30:32.198197+00:00",
  "state_hash": "e2d29aca53dcfeb9"
}
```
- path: `ops/virtual-office/snapshots/LEAD.json`
```json
{
  "agent": "LEAD",
  "last_seq_applied": 51,
  "lease_token": 4,
  "messages_drained": 1,
  "saved_at": "2026-02-19T17:51:07.237073+00:00",
  "state_hash": "7ed8ac97ee628209"
}
```
- path: `ops/virtual-office/snapshots/REX.json`
```json
{
  "agent": "REX",
  "last_seq_applied": 0,
  "lease_token": 1,
  "messages_drained": 0,
  "saved_at": "2026-02-19T22:24:29.700911+00:00",
  "state_hash": "bd4a78bfd4e7d8b1"
}
```
- path: `ops/virtual-office/snapshots/gpt.json`
```json
{
  "agent": "gpt",
  "last_seq_applied": 55,
  "lease_token": 11,
  "messages_drained": 0,
  "saved_at": "2026-02-19T20:58:08.823343+00:00",
  "state_hash": "fd8ad818296c8f87"
}
```
### leases
- path: `ops/virtual-office/leases/--interval.json`
```json
{
  "acquired_at": "2026-02-19T15:02:36.553074+00:00",
  "agent": "--interval",
  "expires_at": "2026-02-19T15:12:36.553098+00:00",
  "lease_token": 8,
  "prev_token": 7,
  "renewed_at": "2026-02-19T15:02:36.553074+00:00",
  "ttl_s": 600
}
```
- path: `ops/virtual-office/leases/B2.json`
```json
{
  "acquired_at": "2026-02-19T17:51:10.269724+00:00",
  "agent": "B2",
  "expires_at": "2026-02-19T18:01:10.269934+00:00",
  "lease_token": 1,
  "prev_token": 0,
  "renewed_at": "2026-02-19T17:51:10.269724+00:00",
  "ttl_s": 600
}
```
- path: `ops/virtual-office/leases/COWORK.json`
```json
{
  "acquired_at": "2026-02-19T14:30:32.193362+00:00",
  "agent": "COWORK",
  "desk_name": "Argos",
  "expires_at": "2026-02-19T14:40:32.193893+00:00",
  "lease_token": 12,
  "prev_token": 11,
  "renewed_at": "2026-02-19T14:30:32.193362+00:00",
  "ttl_s": 600
}
```
- path: `ops/virtual-office/leases/LEAD.json`
```json
{
  "acquired_at": "2026-02-19T17:51:05.165451+00:00",
  "agent": "LEAD",
  "expires_at": "2026-02-19T18:01:05.165791+00:00",
  "lease_token": 4,
  "prev_token": 3,
  "renewed_at": "2026-02-19T17:51:05.165451+00:00",
  "ttl_s": 600
}
```
- path: `ops/virtual-office/leases/REX.json`
```json
{
  "acquired_at": "2026-02-19T22:24:29.698862+00:00",
  "agent": "REX",
  "expires_at": "2026-02-19T22:34:29.699048+00:00",
  "lease_token": 1,
  "prev_token": 0,
  "renewed_at": "2026-02-19T22:24:29.698862+00:00",
  "ttl_s": 600
}
```
- path: `ops/virtual-office/leases/gpt.json`
```json
{
  "acquired_at": "2026-02-19T20:58:08.820939+00:00",
  "agent": "gpt",
  "expires_at": "2026-02-19T21:08:08.820964+00:00",
  "lease_token": 11,
  "prev_token": 10,
  "renewed_at": "2026-02-19T20:58:08.820939+00:00",
  "ttl_s": 600
}
```

## 4) RECENT SIGNALS
- `{"actor":"R1","event_hash":"7a54641de7dda08553d0a3472562ea552b012b0f309e4dee5159011171447544","event_type":"race","payload":{"i":383},"prev_hash":"ef5a7ea14075fd1ca5b091c03de4ed483dd9e55ceea220c7dc8f59f4b0df81fa","timestamp":"2026-02-19T14:30:35.010318+00:00"}`
- `{"actor":"R6","event_hash":"68da677d43a6c4b7ffc0b76ed129c805c2ab10d0c6608ed07e5a0682ead63196","event_type":"race","payload":{"i":380},"prev_hash":"7a54641de7dda08553d0a3472562ea552b012b0f309e4dee5159011171447544","timestamp":"2026-02-19T14:30:35.011079+00:00"}`
- `{"actor":"R2","event_hash":"c1cdcfd368b8c05950e3b0e1cacf67f30ef19b9993dc02c0de4f950a7cf40492","event_type":"race","payload":{"i":378},"prev_hash":"68da677d43a6c4b7ffc0b76ed129c805c2ab10d0c6608ed07e5a0682ead63196","timestamp":"2026-02-19T14:30:35.011819+00:00"}`
- `{"actor":"R3","event_hash":"55159560e64e11258947c0f78246650929277b109369c0ab788fcbe83717efb5","event_type":"race","payload":{"i":379},"prev_hash":"c1cdcfd368b8c05950e3b0e1cacf67f30ef19b9993dc02c0de4f950a7cf40492","timestamp":"2026-02-19T14:30:35.012555+00:00"}`
- `{"actor":"R5","event_hash":"8075be25028dfc165c23e72f27b63c1fa99877a552ffbd1d875f31c7eb446611","event_type":"race","payload":{"i":378},"prev_hash":"55159560e64e11258947c0f78246650929277b109369c0ab788fcbe83717efb5","timestamp":"2026-02-19T14:30:35.013269+00:00"}`
- `{"actor":"R4","event_hash":"5b379bb873ce004bb94a1bc22748f4b248658d33639715745f23b624d4b51018","event_type":"race","payload":{"i":379},"prev_hash":"8075be25028dfc165c23e72f27b63c1fa99877a552ffbd1d875f31c7eb446611","timestamp":"2026-02-19T14:30:35.014022+00:00"}`
- `{"actor":"R1","event_hash":"c6a985d23ccf37d7750dd9b85898ba84ca4316ed7b0ff6303ad899a3d683a16a","event_type":"race","payload":{"i":384},"prev_hash":"5b379bb873ce004bb94a1bc22748f4b248658d33639715745f23b624d4b51018","timestamp":"2026-02-19T14:30:35.014755+00:00"}`
- `{"actor":"R6","event_hash":"0e0d4cf7d27b64caa5c85fbaeabb4d867cff592bf65a60ebe0e12088461578f8","event_type":"race","payload":{"i":381},"prev_hash":"c6a985d23ccf37d7750dd9b85898ba84ca4316ed7b0ff6303ad899a3d683a16a","timestamp":"2026-02-19T14:30:35.015531+00:00"}`
- `{"actor":"R2","event_hash":"189210593f0fa70dbd2cb8f9173aca4d4cf9fcb9489189ff8e10d42d0a1afcf1","event_type":"race","payload":{"i":379},"prev_hash":"0e0d4cf7d27b64caa5c85fbaeabb4d867cff592bf65a60ebe0e12088461578f8","timestamp":"2026-02-19T14:30:35.016278+00:00"}`
- `{"actor":"R3","event_hash":"f3101041c96e7c426e24684e329ce9c843c1201b2c9a57026ca3623641d3ff98","event_type":"race","payload":{"i":380},"prev_hash":"189210593f0fa70dbd2cb8f9173aca4d4cf9fcb9489189ff8e10d42d0a1afcf1","timestamp":"2026-02-19T14:30:35.017016+00:00"}`
- `{"actor":"R5","event_hash":"2f815314c6a660cc5b57b432f093a54d46af9418638d1aab4e18e203014be719","event_type":"race","payload":{"i":379},"prev_hash":"f3101041c96e7c426e24684e329ce9c843c1201b2c9a57026ca3623641d3ff98","timestamp":"2026-02-19T14:30:35.017765+00:00"}`
- `{"actor":"R4","event_hash":"70f143d016bfb3bb45463d56b07f6bb2007fb19c18dd00548346e2c2196d72a2","event_type":"race","payload":{"i":380},"prev_hash":"2f815314c6a660cc5b57b432f093a54d46af9418638d1aab4e18e203014be719","timestamp":"2026-02-19T14:30:35.018498+00:00"}`
- `{"actor":"R1","event_hash":"229e3e5408b116980cf03c8d7c61aa8828035859b30d8b8d939a461fe9c3d4f8","event_type":"race","payload":{"i":385},"prev_hash":"70f143d016bfb3bb45463d56b07f6bb2007fb19c18dd00548346e2c2196d72a2","timestamp":"2026-02-19T14:30:35.019222+00:00"}`
- `{"actor":"R6","event_hash":"7a56ce8af616e10b4c4006546e6b70fdacde2d56fec8850a824242324eabf174","event_type":"race","payload":{"i":382},"prev_hash":"229e3e5408b116980cf03c8d7c61aa8828035859b30d8b8d939a461fe9c3d4f8","timestamp":"2026-02-19T14:30:35.019952+00:00"}`
- `{"actor":"R2","event_hash":"af6d654804cef86f8241c79c62ec2988192c4deb2a364b3d83d6b1553f8f51c4","event_type":"race","payload":{"i":380},"prev_hash":"7a56ce8af616e10b4c4006546e6b70fdacde2d56fec8850a824242324eabf174","timestamp":"2026-02-19T14:30:35.020673+00:00"}`
- `{"actor":"R3","event_hash":"3df103dc501470c8fd5d7190e2658b9cd0ccccb262243fe91191603593ba91a3","event_type":"race","payload":{"i":381},"prev_hash":"af6d654804cef86f8241c79c62ec2988192c4deb2a364b3d83d6b1553f8f51c4","timestamp":"2026-02-19T14:30:35.021408+00:00"}`
- `{"actor":"R5","event_hash":"dab0c992c1688b94f6be2f24976416b5919cbfe80a7b679bd77b7fbdcb00e155","event_type":"race","payload":{"i":380},"prev_hash":"3df103dc501470c8fd5d7190e2658b9cd0ccccb262243fe91191603593ba91a3","timestamp":"2026-02-19T14:30:35.022174+00:00"}`
- `{"actor":"R4","event_hash":"f6354e079775fd6c2c99bdf5334c616b24d577da924238b1f0ec7cd033a487ca","event_type":"race","payload":{"i":381},"prev_hash":"dab0c992c1688b94f6be2f24976416b5919cbfe80a7b679bd77b7fbdcb00e155","timestamp":"2026-02-19T14:30:35.023077+00:00"}`
- `{"actor":"R1","event_hash":"5dc6e37e141ce3168dc2edccab35dac20a132e9a6dadf3447794c9bdda9dc51d","event_type":"race","payload":{"i":386},"prev_hash":"f6354e079775fd6c2c99bdf5334c616b24d577da924238b1f0ec7cd033a487ca","timestamp":"2026-02-19T14:30:35.024010+00:00"}`
- `{"actor":"R6","event_hash":"bcfb2a571caee98bfb0e400c56b0e28384bd170d7fc5b3ba866e45cb7abc5d7f","event_type":"race","payload":{"i":383},"prev_hash":"5dc6e37e141ce3168dc2edccab35dac20a132e9a6dadf3447794c9bdda9dc51d","timestamp":"2026-02-19T14:30:35.024864+00:00"}`
- `{"actor":"R2","event_hash":"d471c41bdab60084b8569a719d6e31be0c2269dfea3f99bf0b11491d2ccd4252","event_type":"race","payload":{"i":381},"prev_hash":"bcfb2a571caee98bfb0e400c56b0e28384bd170d7fc5b3ba866e45cb7abc5d7f","timestamp":"2026-02-19T14:30:35.025703+00:00"}`
- `{"actor":"R3","event_hash":"d6a5226d2cd0afec81174dd6f2048273e9bfa527f6e178a32dd8a0ace678c246","event_type":"race","payload":{"i":382},"prev_hash":"d471c41bdab60084b8569a719d6e31be0c2269dfea3f99bf0b11491d2ccd4252","timestamp":"2026-02-19T14:30:35.026556+00:00"}`
- `{"actor":"R5","event_hash":"15376fd1512e56bd9107218e9eaa12a55f42026d0362f64b0e4774235dd43fd2","event_type":"race","payload":{"i":381},"prev_hash":"d6a5226d2cd0afec81174dd6f2048273e9bfa527f6e178a32dd8a0ace678c246","timestamp":"2026-02-19T14:30:35.027290+00:00"}`
- `{"actor":"R4","event_hash":"0e9cf59e6102b3b45c772490f9ca01a3ad57cc2e6c754a9b5d3f5bdac82f51d2","event_type":"race","payload":{"i":382},"prev_hash":"15376fd1512e56bd9107218e9eaa12a55f42026d0362f64b0e4774235dd43fd2","timestamp":"2026-02-19T14:30:35.028047+00:00"}`
- `{"actor":"R1","event_hash":"17ce07f36cd88d8b4de4f30683bfeed36fe9b097a7cb1b8325e6c3b9817a9719","event_type":"race","payload":{"i":387},"prev_hash":"0e9cf59e6102b3b45c772490f9ca01a3ad57cc2e6c754a9b5d3f5bdac82f51d2","timestamp":"2026-02-19T14:30:35.028803+00:00"}`
- `{"actor":"R6","event_hash":"bcc01c8516955f7f7d5939046e856caa80d1cb68a1604afa3f7540bded955787","event_type":"race","payload":{"i":384},"prev_hash":"17ce07f36cd88d8b4de4f30683bfeed36fe9b097a7cb1b8325e6c3b9817a9719","timestamp":"2026-02-19T14:30:35.029544+00:00"}`
- `{"actor":"R2","event_hash":"257a777a6e13c0946947d8c342691e2d547fff8b83eab4b31f62b6b217abbafb","event_type":"race","payload":{"i":382},"prev_hash":"bcc01c8516955f7f7d5939046e856caa80d1cb68a1604afa3f7540bded955787","timestamp":"2026-02-19T14:30:35.030332+00:00"}`
- `{"actor":"R3","event_hash":"41fdb18cba7196366490e82690fc02480e7ccac62ea3aaf2aa41332844e17fa9","event_type":"race","payload":{"i":383},"prev_hash":"257a777a6e13c0946947d8c342691e2d547fff8b83eab4b31f62b6b217abbafb","timestamp":"2026-02-19T14:30:35.031121+00:00"}`
- `{"actor":"R5","event_hash":"ceea30a649f04e83e1e7a52ba52c8247361cb758340e36e89e88d0f4e65516bd","event_type":"race","payload":{"i":382},"prev_hash":"41fdb18cba7196366490e82690fc02480e7ccac62ea3aaf2aa41332844e17fa9","timestamp":"2026-02-19T14:30:35.031920+00:00"}`
- `{"actor":"R4","event_hash":"c015bdfbe949281400ac6067debf452b81e7e58ae6ffb68ffe6dcebfdcb02084","event_type":"race","payload":{"i":383},"prev_hash":"ceea30a649f04e83e1e7a52ba52c8247361cb758340e36e89e88d0f4e65516bd","timestamp":"2026-02-19T14:30:35.032806+00:00"}`
- `{"actor":"R1","event_hash":"7fb51e2525d7fb077c02884ea6d5e62952433c7ab9d5ba59156cfd6f88e41fb2","event_type":"race","payload":{"i":388},"prev_hash":"c015bdfbe949281400ac6067debf452b81e7e58ae6ffb68ffe6dcebfdcb02084","timestamp":"2026-02-19T14:30:35.033595+00:00"}`
- `{"actor":"R6","event_hash":"7465b6a849825e3479e7805b79ccbd7515a317d628a6bb254f15f76e06884ec7","event_type":"race","payload":{"i":385},"prev_hash":"7fb51e2525d7fb077c02884ea6d5e62952433c7ab9d5ba59156cfd6f88e41fb2","timestamp":"2026-02-19T14:30:35.034356+00:00"}`
- `{"actor":"R2","event_hash":"d02a497c49498c1f6924c475f919586beaabdbc21c329a630a0e3d82094e4dee","event_type":"race","payload":{"i":383},"prev_hash":"7465b6a849825e3479e7805b79ccbd7515a317d628a6bb254f15f76e06884ec7","timestamp":"2026-02-19T14:30:35.035105+00:00"}`
- `{"actor":"R3","event_hash":"f544c1698af51eff8f6ed50c2e685505a4633ed379a627a49495312185e7bcb0","event_type":"race","payload":{"i":384},"prev_hash":"d02a497c49498c1f6924c475f919586beaabdbc21c329a630a0e3d82094e4dee","timestamp":"2026-02-19T14:30:35.035901+00:00"}`
- `{"actor":"R5","event_hash":"57e1b0d4892b6f03fa05a0e3c8b798df74aa7c096d552164f2df8fb7edea12c0","event_type":"race","payload":{"i":383},"prev_hash":"f544c1698af51eff8f6ed50c2e685505a4633ed379a627a49495312185e7bcb0","timestamp":"2026-02-19T14:30:35.036657+00:00"}`
- `{"actor":"R4","event_hash":"a7d4d2689c7a5d2bf8268dbb013afa1553c4008c898c1cf72425ed57fbcdb52e","event_type":"race","payload":{"i":384},"prev_hash":"57e1b0d4892b6f03fa05a0e3c8b798df74aa7c096d552164f2df8fb7edea12c0","timestamp":"2026-02-19T14:30:35.037407+00:00"}`
- `{"actor":"R1","event_hash":"c0e3de20283da196074b18175059f9fac753a97e713ae612be4ee17adb5b5438","event_type":"race","payload":{"i":389},"prev_hash":"a7d4d2689c7a5d2bf8268dbb013afa1553c4008c898c1cf72425ed57fbcdb52e","timestamp":"2026-02-19T14:30:35.038171+00:00"}`
- `{"actor":"R6","event_hash":"525d66913e315689aa25f36e09bf55be1890290a62c081e2c7fd1fc2d1cde7ea","event_type":"race","payload":{"i":386},"prev_hash":"c0e3de20283da196074b18175059f9fac753a97e713ae612be4ee17adb5b5438","timestamp":"2026-02-19T14:30:35.038921+00:00"}`
- `{"actor":"R2","event_hash":"8fe71d3c83b0fbc38681527cc0fb92e739e17e8a21f1e61861d676b0a66edce2","event_type":"race","payload":{"i":384},"prev_hash":"525d66913e315689aa25f36e09bf55be1890290a62c081e2c7fd1fc2d1cde7ea","timestamp":"2026-02-19T14:30:35.039855+00:00"}`
- `{"actor":"R3","event_hash":"cc7aa87380b28c638bc921e64f2ae080c5563d61c416650651bd68da9cd34e53","event_type":"race","payload":{"i":385},"prev_hash":"8fe71d3c83b0fbc38681527cc0fb92e739e17e8a21f1e61861d676b0a66edce2","timestamp":"2026-02-19T14:30:35.040813+00:00"}`
- `{"actor":"R5","event_hash":"d04d1211ea77ef7b614cd79d56d01617fb16740bdad02bdd9c0fe43edc6c344c","event_type":"race","payload":{"i":384},"prev_hash":"cc7aa87380b28c638bc921e64f2ae080c5563d61c416650651bd68da9cd34e53","timestamp":"2026-02-19T14:30:35.041709+00:00"}`
- `{"actor":"R4","event_hash":"e13ca109a3658637b5b1452539610146bff9df888875a1e16c97303a3bfddc26","event_type":"race","payload":{"i":385},"prev_hash":"d04d1211ea77ef7b614cd79d56d01617fb16740bdad02bdd9c0fe43edc6c344c","timestamp":"2026-02-19T14:30:35.042529+00:00"}`
- `{"actor":"R1","event_hash":"cf74e59978ed8a6a213d2e0d2518dc9cb3a3ab7687087e2bee24c5f8bfd38fe4","event_type":"race","payload":{"i":390},"prev_hash":"e13ca109a3658637b5b1452539610146bff9df888875a1e16c97303a3bfddc26","timestamp":"2026-02-19T14:30:35.043329+00:00"}`
- `{"actor":"R6","event_hash":"efe21097bd5b2aee0325d2370f9a7a8fa2a7bc6dabc1a8c4f2c866e21a0d95f8","event_type":"race","payload":{"i":387},"prev_hash":"cf74e59978ed8a6a213d2e0d2518dc9cb3a3ab7687087e2bee24c5f8bfd38fe4","timestamp":"2026-02-19T14:30:35.044130+00:00"}`
- `{"actor":"R2","event_hash":"7d7b4447427110402d65b4a6652d112b661c09d3072ca20f4ea4d94e4dbf262d","event_type":"race","payload":{"i":385},"prev_hash":"efe21097bd5b2aee0325d2370f9a7a8fa2a7bc6dabc1a8c4f2c866e21a0d95f8","timestamp":"2026-02-19T14:30:35.044930+00:00"}`
- `{"actor":"R3","event_hash":"46c1884fef12a50c75bd5caa73a111ccb65ef5ea37dd681a0ad76729c2489a90","event_type":"race","payload":{"i":386},"prev_hash":"7d7b4447427110402d65b4a6652d112b661c09d3072ca20f4ea4d94e4dbf262d","timestamp":"2026-02-19T14:30:35.045734+00:00"}`
- `{"actor":"R5","event_hash":"983728807fa2d0f18fc8ff82f0932a7d05db053ee2dc0616dc7906af722fb570","event_type":"race","payload":{"i":385},"prev_hash":"46c1884fef12a50c75bd5caa73a111ccb65ef5ea37dd681a0ad76729c2489a90","timestamp":"2026-02-19T14:30:35.046536+00:00"}`
- `{"actor":"R4","event_hash":"3c21cb74fdc22a0351e5008919e5f9cd9b615b124eb8384378bb943909584f78","event_type":"race","payload":{"i":386},"prev_hash":"983728807fa2d0f18fc8ff82f0932a7d05db053ee2dc0616dc7906af722fb570","timestamp":"2026-02-19T14:30:35.047306+00:00"}`
- `{"actor":"R1","event_hash":"69af4b567bedb5f869b90ebf17c0fcb2a4eb5dd17e62a0bc36b4059567864f4f","event_type":"race","payload":{"i":391},"prev_hash":"3c21cb74fdc22a0351e5008919e5f9cd9b615b124eb8384378bb943909584f78","timestamp":"2026-02-19T14:30:35.048077+00:00"}`
- `{"actor":"R6","event_hash":"1521bad8d528d1bbee87f2d2588ae59ec021d60d55ae39c9229e2753175984de","event_type":"race","payload":{"i":388},"prev_hash":"69af4b567bedb5f869b90ebf17c0fcb2a4eb5dd17e62a0bc36b4059567864f4f","timestamp":"2026-02-19T14:30:35.048826+00:00"}`
- `{"actor":"R2","event_hash":"05770fc36adc41b8844f878b584ed34c8a52d11f3815a7a45df986c6931da111","event_type":"race","payload":{"i":386},"prev_hash":"1521bad8d528d1bbee87f2d2588ae59ec021d60d55ae39c9229e2753175984de","timestamp":"2026-02-19T14:30:35.049584+00:00"}`
- `{"actor":"R3","event_hash":"760082134c0595e169dd34976b28976c8c3d878744d3cd8b4aeb78c16301989f","event_type":"race","payload":{"i":387},"prev_hash":"05770fc36adc41b8844f878b584ed34c8a52d11f3815a7a45df986c6931da111","timestamp":"2026-02-19T14:30:35.050355+00:00"}`
- `{"actor":"R5","event_hash":"5e594a38b68f2105233724378b1d5e6693392729dfdc786513da6487ad4b8bc6","event_type":"race","payload":{"i":386},"prev_hash":"760082134c0595e169dd34976b28976c8c3d878744d3cd8b4aeb78c16301989f","timestamp":"2026-02-19T14:30:35.051110+00:00"}`
- `{"actor":"R4","event_hash":"96c5312577f06f375684cc857634c20e0da70de343454ade9426a4caecb7d86b","event_type":"race","payload":{"i":387},"prev_hash":"5e594a38b68f2105233724378b1d5e6693392729dfdc786513da6487ad4b8bc6","timestamp":"2026-02-19T14:30:35.051869+00:00"}`
- `{"actor":"R1","event_hash":"fb6a2ad837a60cd54ee7345469917b6b53266356c9818f6d96cb0b67b539abf8","event_type":"race","payload":{"i":392},"prev_hash":"96c5312577f06f375684cc857634c20e0da70de343454ade9426a4caecb7d86b","timestamp":"2026-02-19T14:30:35.052605+00:00"}`
- `{"actor":"R6","event_hash":"16e826b115443d9712a179e18fa51c1d649f5a53a74e79f1dfacc4223f598f4d","event_type":"race","payload":{"i":389},"prev_hash":"fb6a2ad837a60cd54ee7345469917b6b53266356c9818f6d96cb0b67b539abf8","timestamp":"2026-02-19T14:30:35.053354+00:00"}`
- `{"actor":"R2","event_hash":"51e1384e5b4b513d9d200fca7ff469484133fe0d5438e2fec7e462c8bc111f5c","event_type":"race","payload":{"i":387},"prev_hash":"16e826b115443d9712a179e18fa51c1d649f5a53a74e79f1dfacc4223f598f4d","timestamp":"2026-02-19T14:30:35.054089+00:00"}`
- `{"actor":"R3","event_hash":"c9f0d89e5b59ec1bce774903094c32ea24cb7557a882f279f63b124ea2643641","event_type":"race","payload":{"i":388},"prev_hash":"51e1384e5b4b513d9d200fca7ff469484133fe0d5438e2fec7e462c8bc111f5c","timestamp":"2026-02-19T14:30:35.054826+00:00"}`
- `{"actor":"R5","event_hash":"1744ecca716b96755b4a35891e079ff224338d6642665057d055d06dc63b1f4c","event_type":"race","payload":{"i":387},"prev_hash":"c9f0d89e5b59ec1bce774903094c32ea24cb7557a882f279f63b124ea2643641","timestamp":"2026-02-19T14:30:35.055622+00:00"}`
- `{"actor":"R4","event_hash":"2d1eb5ba8f1f8ea3d1eaee0f88048e59a3807200c0796a999d6aef4881a47d3c","event_type":"race","payload":{"i":388},"prev_hash":"1744ecca716b96755b4a35891e079ff224338d6642665057d055d06dc63b1f4c","timestamp":"2026-02-19T14:30:35.056526+00:00"}`
- `{"actor":"R1","event_hash":"6cde20880d3267f89f53ce9ff9440cac6d2dfd561691f46597903a81c6520bc3","event_type":"race","payload":{"i":393},"prev_hash":"2d1eb5ba8f1f8ea3d1eaee0f88048e59a3807200c0796a999d6aef4881a47d3c","timestamp":"2026-02-19T14:30:35.057419+00:00"}`
- `{"actor":"R6","event_hash":"9aa1013359555fd40fff41e2826044ddb887b1a2cc04cb1783e3d8dd7a9fe820","event_type":"race","payload":{"i":390},"prev_hash":"6cde20880d3267f89f53ce9ff9440cac6d2dfd561691f46597903a81c6520bc3","timestamp":"2026-02-19T14:30:35.058300+00:00"}`
- `{"actor":"R2","event_hash":"c9053dd68ca43f89a327f53f19797334eabddf9cebee54d10cbf37472fb35343","event_type":"race","payload":{"i":388},"prev_hash":"9aa1013359555fd40fff41e2826044ddb887b1a2cc04cb1783e3d8dd7a9fe820","timestamp":"2026-02-19T14:30:35.059183+00:00"}`
- `{"actor":"R3","event_hash":"c4420e49ffb72acdbae9ea9e27d92926d5f82a5e069e65ab1ae2c7f51b37a81e","event_type":"race","payload":{"i":389},"prev_hash":"c9053dd68ca43f89a327f53f19797334eabddf9cebee54d10cbf37472fb35343","timestamp":"2026-02-19T14:30:35.059989+00:00"}`
- `{"actor":"R5","event_hash":"ef1c8beec6e482ffe7622d0eb275d6a254308a14d1f0fc3bda0ed5c0baea258f","event_type":"race","payload":{"i":388},"prev_hash":"c4420e49ffb72acdbae9ea9e27d92926d5f82a5e069e65ab1ae2c7f51b37a81e","timestamp":"2026-02-19T14:30:35.060774+00:00"}`
- `{"actor":"R4","event_hash":"21b48f8da97c2c4d48ec496ff25ec872babd9e13da366952fd59a9fd16ac77b4","event_type":"race","payload":{"i":389},"prev_hash":"ef1c8beec6e482ffe7622d0eb275d6a254308a14d1f0fc3bda0ed5c0baea258f","timestamp":"2026-02-19T14:30:35.061572+00:00"}`
- `{"actor":"R1","event_hash":"ee105764ba93b8168ea0ebcd060b399a18fd3a6a5201c345726bfb439c57e90d","event_type":"race","payload":{"i":394},"prev_hash":"21b48f8da97c2c4d48ec496ff25ec872babd9e13da366952fd59a9fd16ac77b4","timestamp":"2026-02-19T14:30:35.062390+00:00"}`
- `{"actor":"R6","event_hash":"53e1263379995312d69d6faa2093c7bdc97c909b2b0b095332d33bd3cf059a27","event_type":"race","payload":{"i":391},"prev_hash":"ee105764ba93b8168ea0ebcd060b399a18fd3a6a5201c345726bfb439c57e90d","timestamp":"2026-02-19T14:30:35.063167+00:00"}`
- `{"actor":"R2","event_hash":"18b96a89c465d1887ab7bd1e80e29f01b540b17f23588fb2e535527ed17a438e","event_type":"race","payload":{"i":389},"prev_hash":"53e1263379995312d69d6faa2093c7bdc97c909b2b0b095332d33bd3cf059a27","timestamp":"2026-02-19T14:30:35.063946+00:00"}`
- `{"actor":"R3","event_hash":"a5f3470f04ddceacc24091e542f9926e0776f3afe3f69c439083032bcd2fd326","event_type":"race","payload":{"i":390},"prev_hash":"18b96a89c465d1887ab7bd1e80e29f01b540b17f23588fb2e535527ed17a438e","timestamp":"2026-02-19T14:30:35.064718+00:00"}`
- `{"actor":"R5","event_hash":"5db792b372c8cdcf5ab9e5f31c3091410dbf6af2b79df3786e64bbe8a7fc3f94","event_type":"race","payload":{"i":389},"prev_hash":"a5f3470f04ddceacc24091e542f9926e0776f3afe3f69c439083032bcd2fd326","timestamp":"2026-02-19T14:30:35.065483+00:00"}`
- `{"actor":"R4","event_hash":"54f6813dff5c0608bdb0973014d44b237f46f6016c4a78e9b861c169fbe901ab","event_type":"race","payload":{"i":390},"prev_hash":"5db792b372c8cdcf5ab9e5f31c3091410dbf6af2b79df3786e64bbe8a7fc3f94","timestamp":"2026-02-19T14:30:35.066243+00:00"}`
- `{"actor":"R1","event_hash":"afde80ff0b34e6f3cc618737e52c730114093dc86e73f691096bbe02407994fc","event_type":"race","payload":{"i":395},"prev_hash":"54f6813dff5c0608bdb0973014d44b237f46f6016c4a78e9b861c169fbe901ab","timestamp":"2026-02-19T14:30:35.067036+00:00"}`
- `{"actor":"R6","event_hash":"7e1cb8b5c4cbb5e70ee37145997ce6b583c3f41cfda0a49fd6e08fa9d6613879","event_type":"race","payload":{"i":392},"prev_hash":"afde80ff0b34e6f3cc618737e52c730114093dc86e73f691096bbe02407994fc","timestamp":"2026-02-19T14:30:35.067852+00:00"}`
- `{"actor":"R2","event_hash":"be1075b3e833d24c28326c87c30593f533590199c4c03b04417a000d1333cd52","event_type":"race","payload":{"i":390},"prev_hash":"7e1cb8b5c4cbb5e70ee37145997ce6b583c3f41cfda0a49fd6e08fa9d6613879","timestamp":"2026-02-19T14:30:35.068689+00:00"}`
- `{"actor":"R3","event_hash":"1ea99e87d3a106b55f78a874c159b84b91e0d16f40f816b131c9ae89b444088c","event_type":"race","payload":{"i":391},"prev_hash":"be1075b3e833d24c28326c87c30593f533590199c4c03b04417a000d1333cd52","timestamp":"2026-02-19T14:30:35.069469+00:00"}`
- `{"actor":"R5","event_hash":"0265a32efb07bb0014ace0c9ee03ef1b7cc6ebfc71ea6a1bba95e87d55b4ad49","event_type":"race","payload":{"i":390},"prev_hash":"1ea99e87d3a106b55f78a874c159b84b91e0d16f40f816b131c9ae89b444088c","timestamp":"2026-02-19T14:30:35.070215+00:00"}`
- `{"actor":"R4","event_hash":"a398566286ffde1eb98edbb30617cc51f9d0e600b0b62a3a56469fc22c5adb59","event_type":"race","payload":{"i":391},"prev_hash":"0265a32efb07bb0014ace0c9ee03ef1b7cc6ebfc71ea6a1bba95e87d55b4ad49","timestamp":"2026-02-19T14:30:35.070969+00:00"}`
- `{"actor":"R1","event_hash":"04aaf616a0d153b8e08e51e3a1eac935b8e6122e939bec9924a46f83996c2497","event_type":"race","payload":{"i":396},"prev_hash":"a398566286ffde1eb98edbb30617cc51f9d0e600b0b62a3a56469fc22c5adb59","timestamp":"2026-02-19T14:30:35.071690+00:00"}`
- `{"actor":"R6","event_hash":"c70bb44a9038eab5484fb0e1c7eac5ca20017e6b482b1960f7b69487a6195be7","event_type":"race","payload":{"i":393},"prev_hash":"04aaf616a0d153b8e08e51e3a1eac935b8e6122e939bec9924a46f83996c2497","timestamp":"2026-02-19T14:30:35.072471+00:00"}`
- `{"actor":"R2","event_hash":"99429c2f7a16261d9f6616f36754b2b1daf3b653d93a5abf17e4c23de03baba7","event_type":"race","payload":{"i":391},"prev_hash":"c70bb44a9038eab5484fb0e1c7eac5ca20017e6b482b1960f7b69487a6195be7","timestamp":"2026-02-19T14:30:35.073382+00:00"}`
- `{"actor":"R3","event_hash":"51f9c24be5d5c3026343d8744350dac384a8c5afed89ecfe8123d2540e0ce181","event_type":"race","payload":{"i":392},"prev_hash":"99429c2f7a16261d9f6616f36754b2b1daf3b653d93a5abf17e4c23de03baba7","timestamp":"2026-02-19T14:30:35.074195+00:00"}`
- `{"actor":"R5","event_hash":"c79183f8cc0dbaf331cfa5446a3927e41889c32d92f7b8f6f782e8ff6607dc23","event_type":"race","payload":{"i":391},"prev_hash":"51f9c24be5d5c3026343d8744350dac384a8c5afed89ecfe8123d2540e0ce181","timestamp":"2026-02-19T14:30:35.075018+00:00"}`
- `{"actor":"R4","event_hash":"07613cd35e17de73e442a64629f45ca943e9e1c42cda345c698228f0119ee539","event_type":"race","payload":{"i":392},"prev_hash":"c79183f8cc0dbaf331cfa5446a3927e41889c32d92f7b8f6f782e8ff6607dc23","timestamp":"2026-02-19T14:30:35.075898+00:00"}`
- `{"actor":"R1","event_hash":"7ddeba094f3efcda4d06b296f05b074df9aff211d2c8192354a15f44282217fb","event_type":"race","payload":{"i":397},"prev_hash":"07613cd35e17de73e442a64629f45ca943e9e1c42cda345c698228f0119ee539","timestamp":"2026-02-19T14:30:35.076794+00:00"}`
- `{"actor":"R6","event_hash":"d9664fea7290a9328911f5df005290d30b00d94040837e327507ec304873dc01","event_type":"race","payload":{"i":394},"prev_hash":"7ddeba094f3efcda4d06b296f05b074df9aff211d2c8192354a15f44282217fb","timestamp":"2026-02-19T14:30:35.077624+00:00"}`
- `{"actor":"R2","event_hash":"8e6b8cf26c37d7323fa23fcd7f597f4e5136a1bba9af9bad019912ce29f59846","event_type":"race","payload":{"i":392},"prev_hash":"d9664fea7290a9328911f5df005290d30b00d94040837e327507ec304873dc01","timestamp":"2026-02-19T14:30:35.078436+00:00"}`
- `{"actor":"R3","event_hash":"d40a51605b69431590b60dc8a71035bffd7d6b516a91b32047b29d9de32422d6","event_type":"race","payload":{"i":393},"prev_hash":"8e6b8cf26c37d7323fa23fcd7f597f4e5136a1bba9af9bad019912ce29f59846","timestamp":"2026-02-19T14:30:35.079267+00:00"}`
- `{"actor":"R5","event_hash":"d0aeb6d1c653394ded06a70c91763cd4f8a57871a70acab622e8adfc0300188d","event_type":"race","payload":{"i":392},"prev_hash":"d40a51605b69431590b60dc8a71035bffd7d6b516a91b32047b29d9de32422d6","timestamp":"2026-02-19T14:30:35.080086+00:00"}`
- `{"actor":"R4","event_hash":"e15056d7734d2abd534ceaad65d125f80c7269f664f9ced17d1f1f8ea24d8c58","event_type":"race","payload":{"i":393},"prev_hash":"d0aeb6d1c653394ded06a70c91763cd4f8a57871a70acab622e8adfc0300188d","timestamp":"2026-02-19T14:30:35.080852+00:00"}`
- `{"actor":"R1","event_hash":"26c3c4affa420d2cee4a662db3fd84017ba4317b37c0d33cc4ecc5d42dcd35e4","event_type":"race","payload":{"i":398},"prev_hash":"e15056d7734d2abd534ceaad65d125f80c7269f664f9ced17d1f1f8ea24d8c58","timestamp":"2026-02-19T14:30:35.081607+00:00"}`
- `{"actor":"R6","event_hash":"68b30292a5c0271010ed882d8fd739a0f9835904392cade2b1fe349e06f927e1","event_type":"race","payload":{"i":395},"prev_hash":"26c3c4affa420d2cee4a662db3fd84017ba4317b37c0d33cc4ecc5d42dcd35e4","timestamp":"2026-02-19T14:30:35.082359+00:00"}`
- `{"actor":"R2","event_hash":"1c9aa4d075a4d13c0b22cd49bab1cccb826467f0dd11fa6edf549bcc2554bd63","event_type":"race","payload":{"i":393},"prev_hash":"68b30292a5c0271010ed882d8fd739a0f9835904392cade2b1fe349e06f927e1","timestamp":"2026-02-19T14:30:35.083106+00:00"}`
- `{"actor":"R3","event_hash":"59309cb313c551e37ee729500fd4f51bf10dea3a16d0633df6cddb20c3fc5383","event_type":"race","payload":{"i":394},"prev_hash":"1c9aa4d075a4d13c0b22cd49bab1cccb826467f0dd11fa6edf549bcc2554bd63","timestamp":"2026-02-19T14:30:35.083863+00:00"}`
- `{"actor":"R5","event_hash":"21b7b2342c28ac1f0ce89241cd0d46fddf4b6b691a8c4543ccfd2742980a23dc","event_type":"race","payload":{"i":393},"prev_hash":"59309cb313c551e37ee729500fd4f51bf10dea3a16d0633df6cddb20c3fc5383","timestamp":"2026-02-19T14:30:35.084623+00:00"}`
- `{"actor":"R4","event_hash":"5a21fcaba7f16cf7549802fa4585d24fa5b8d86a481159f70e0a06dedac4e15b","event_type":"race","payload":{"i":394},"prev_hash":"21b7b2342c28ac1f0ce89241cd0d46fddf4b6b691a8c4543ccfd2742980a23dc","timestamp":"2026-02-19T14:30:35.085420+00:00"}`
- `{"actor":"R1","event_hash":"0470aa054ccf1c159835f5da188936e04f80b1f3062ff7e9fba4027eb4218542","event_type":"race","payload":{"i":399},"prev_hash":"5a21fcaba7f16cf7549802fa4585d24fa5b8d86a481159f70e0a06dedac4e15b","timestamp":"2026-02-19T14:30:35.086246+00:00"}`
- `{"actor":"R6","event_hash":"5e582fb409c2d05ebb628182ec7de8652d8927d9480097804786b5f653acd42f","event_type":"race","payload":{"i":396},"prev_hash":"0470aa054ccf1c159835f5da188936e04f80b1f3062ff7e9fba4027eb4218542","timestamp":"2026-02-19T14:30:35.087035+00:00"}`
- `{"actor":"R2","event_hash":"d1b879da110219c974c71bd7f559e6382d74415d0d598ccc5e31b86a7e0b2347","event_type":"race","payload":{"i":394},"prev_hash":"5e582fb409c2d05ebb628182ec7de8652d8927d9480097804786b5f653acd42f","timestamp":"2026-02-19T14:30:35.087802+00:00"}`
- `{"actor":"R3","event_hash":"b92a977245aef278dd2a9662917c5f355c857114c13366d748ca919983d685cd","event_type":"race","payload":{"i":395},"prev_hash":"d1b879da110219c974c71bd7f559e6382d74415d0d598ccc5e31b86a7e0b2347","timestamp":"2026-02-19T14:30:35.088555+00:00"}`
- `{"actor":"R5","event_hash":"c6f8dfc7256af7a058af38221a44cf34c37419f7f6722c8fbb50952ea9b59b59","event_type":"race","payload":{"i":394},"prev_hash":"b92a977245aef278dd2a9662917c5f355c857114c13366d748ca919983d685cd","timestamp":"2026-02-19T14:30:35.089341+00:00"}`
- `{"actor":"R4","event_hash":"d4b163afa28a4b725713aec0e13046ad3f9bab9e445cf137cb571e261c9b38f4","event_type":"race","payload":{"i":395},"prev_hash":"c6f8dfc7256af7a058af38221a44cf34c37419f7f6722c8fbb50952ea9b59b59","timestamp":"2026-02-19T14:30:35.090534+00:00"}`
- `{"actor":"R6","event_hash":"44390fb43cc855d9d97d1712ea528d2484ae930fec15ac206a300534322af5ed","event_type":"race","payload":{"i":397},"prev_hash":"d4b163afa28a4b725713aec0e13046ad3f9bab9e445cf137cb571e261c9b38f4","timestamp":"2026-02-19T14:30:35.091554+00:00"}`
- `{"actor":"R2","event_hash":"6331555dbc98aa897b0c67a0e05fceac639087ab432c6bc2d67696905c9f0a2f","event_type":"race","payload":{"i":395},"prev_hash":"44390fb43cc855d9d97d1712ea528d2484ae930fec15ac206a300534322af5ed","timestamp":"2026-02-19T14:30:35.092557+00:00"}`
- `{"actor":"R3","event_hash":"df53fc4f4e5efcf7d804f8939c5ea1c6cd2947acdd234450f46102daf530b594","event_type":"race","payload":{"i":396},"prev_hash":"6331555dbc98aa897b0c67a0e05fceac639087ab432c6bc2d67696905c9f0a2f","timestamp":"2026-02-19T14:30:35.093507+00:00"}`
- `{"actor":"R5","event_hash":"257d3559b8494bdaeff802c791adf115ec6e7913a5844284d603baa25fb63c14","event_type":"race","payload":{"i":395},"prev_hash":"df53fc4f4e5efcf7d804f8939c5ea1c6cd2947acdd234450f46102daf530b594","timestamp":"2026-02-19T14:30:35.094524+00:00"}`
- `{"actor":"R4","event_hash":"7195785448c1e02113c2bdd5dcfbf64f1a27ab2e31163bff9c3cd65cf9527980","event_type":"race","payload":{"i":396},"prev_hash":"257d3559b8494bdaeff802c791adf115ec6e7913a5844284d603baa25fb63c14","timestamp":"2026-02-19T14:30:35.095432+00:00"}`
- `{"actor":"R6","event_hash":"3d4af0e72229b3b50976fb69adbb646d730ad2d0d16e8fe3f4cfa0d13f0898b4","event_type":"race","payload":{"i":398},"prev_hash":"7195785448c1e02113c2bdd5dcfbf64f1a27ab2e31163bff9c3cd65cf9527980","timestamp":"2026-02-19T14:30:35.096341+00:00"}`
- `{"actor":"R2","event_hash":"f2fbc290c6a9a5d0801c2ff3d0b0c61434ab2857400a01f6cbd0c67f2c5d4267","event_type":"race","payload":{"i":396},"prev_hash":"3d4af0e72229b3b50976fb69adbb646d730ad2d0d16e8fe3f4cfa0d13f0898b4","timestamp":"2026-02-19T14:30:35.097263+00:00"}`
- `{"actor":"R3","event_hash":"38dafb5392d786ef1658d58d46c595bd3d1f399a75080a7bcc51142a2f9559d8","event_type":"race","payload":{"i":397},"prev_hash":"f2fbc290c6a9a5d0801c2ff3d0b0c61434ab2857400a01f6cbd0c67f2c5d4267","timestamp":"2026-02-19T14:30:35.098057+00:00"}`
- `{"actor":"R5","event_hash":"34cc00e61c3d3b4f89b0a40c84df71adc766045ab6805beac9dcf95f2a8eb25b","event_type":"race","payload":{"i":396},"prev_hash":"38dafb5392d786ef1658d58d46c595bd3d1f399a75080a7bcc51142a2f9559d8","timestamp":"2026-02-19T14:30:35.098810+00:00"}`
- `{"actor":"R4","event_hash":"e32eb2566766c0d262a71b28c7be214aae521a9e9d760459cfdf36ebbffafddd","event_type":"race","payload":{"i":397},"prev_hash":"34cc00e61c3d3b4f89b0a40c84df71adc766045ab6805beac9dcf95f2a8eb25b","timestamp":"2026-02-19T14:30:35.099527+00:00"}`
- `{"actor":"R6","event_hash":"3a2cca4025b76956fa4d96b8df24f621e9ebd7e71c8a43e8446ce4b90274aa03","event_type":"race","payload":{"i":399},"prev_hash":"e32eb2566766c0d262a71b28c7be214aae521a9e9d760459cfdf36ebbffafddd","timestamp":"2026-02-19T14:30:35.100296+00:00"}`
- `{"actor":"R2","event_hash":"23d161948da8a8291dca29f57b78e6cf0017a27b61be96549174b5ad9686bb99","event_type":"race","payload":{"i":397},"prev_hash":"3a2cca4025b76956fa4d96b8df24f621e9ebd7e71c8a43e8446ce4b90274aa03","timestamp":"2026-02-19T14:30:35.101008+00:00"}`
- `{"actor":"R3","event_hash":"e338b5efa1ced8f00d7c8c820c2529dcd7c146469721f238d635c9c4ef47bb40","event_type":"race","payload":{"i":398},"prev_hash":"23d161948da8a8291dca29f57b78e6cf0017a27b61be96549174b5ad9686bb99","timestamp":"2026-02-19T14:30:35.101800+00:00"}`
- `{"actor":"R5","event_hash":"93bb15bd815540f69680d7b697b776885a36e9c5d62ba87d6f765c8e7556745c","event_type":"race","payload":{"i":397},"prev_hash":"e338b5efa1ced8f00d7c8c820c2529dcd7c146469721f238d635c9c4ef47bb40","timestamp":"2026-02-19T14:30:35.102601+00:00"}`
- `{"actor":"R4","event_hash":"770aaa86d618c80344eb2b1132df7e3130a4050e5837e404d0c4fce33423208a","event_type":"race","payload":{"i":398},"prev_hash":"93bb15bd815540f69680d7b697b776885a36e9c5d62ba87d6f765c8e7556745c","timestamp":"2026-02-19T14:30:35.103418+00:00"}`
- `{"actor":"R2","event_hash":"652cae1872730d08846b76ef8b25315e122c4f39fd91360f92e1846c5e86e1ba","event_type":"race","payload":{"i":398},"prev_hash":"770aaa86d618c80344eb2b1132df7e3130a4050e5837e404d0c4fce33423208a","timestamp":"2026-02-19T14:30:35.104231+00:00"}`
- `{"actor":"R3","event_hash":"9c6fa63b2cd1cad02aa01392f31640c3fda40e875de4552337b8dedc4fc67f29","event_type":"race","payload":{"i":399},"prev_hash":"652cae1872730d08846b76ef8b25315e122c4f39fd91360f92e1846c5e86e1ba","timestamp":"2026-02-19T14:30:35.105066+00:00"}`
- `{"actor":"R5","event_hash":"5108a4558c91e2d13265eb3371b44ce9a5f6c0772bed10422c114fe566d656a8","event_type":"race","payload":{"i":398},"prev_hash":"9c6fa63b2cd1cad02aa01392f31640c3fda40e875de4552337b8dedc4fc67f29","timestamp":"2026-02-19T14:30:35.106659+00:00"}`
- `{"actor":"R4","event_hash":"bd05c20d2dddeef5ee4bd91075392853065a4264991c2c948442bfbf259fced9","event_type":"race","payload":{"i":399},"prev_hash":"5108a4558c91e2d13265eb3371b44ce9a5f6c0772bed10422c114fe566d656a8","timestamp":"2026-02-19T14:30:35.107784+00:00"}`
- `{"actor":"R2","event_hash":"5c484a4870468fdd96a45a4c38cfed8486bb8af76f8cbea473e7a970cf12b74b","event_type":"race","payload":{"i":399},"prev_hash":"bd05c20d2dddeef5ee4bd91075392853065a4264991c2c948442bfbf259fced9","timestamp":"2026-02-19T14:30:35.109019+00:00"}`
- `{"actor":"R5","event_hash":"5aea7a59eb3910b9d52cbef8586a1b4fd9f8cfd7ab7f4209c358f45599adcb8e","event_type":"race","payload":{"i":399},"prev_hash":"5c484a4870468fdd96a45a4c38cfed8486bb8af76f8cbea473e7a970cf12b74b","timestamp":"2026-02-19T14:30:35.110104+00:00"}`
- `{"actor":"--interval","event_hash":"5bc4e284fd2dc4b46ac09fe6df72565f22f6a45e876ae4f51256d224c0f69dd3","event_type":"lease.acquire","payload":{"lease_token":1,"prev_token":0,"ttl_s":600},"prev_hash":"5aea7a59eb3910b9d52cbef8586a1b4fd9f8cfd7ab7f4209c358f45599adcb8e","timestamp":"2026-02-19T14:45:26.329708+00:00"}`
- `{"actor":"--interval","event_hash":"6ffb3956bf9b16c93b8169bcee282f66ec0e18bbf68bdb74eb0d9380f395ac9f","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":1,"msgs":0},"prev_hash":"5bc4e284fd2dc4b46ac09fe6df72565f22f6a45e876ae4f51256d224c0f69dd3","timestamp":"2026-02-19T14:45:26.330766+00:00"}`
- `{"actor":"--interval","event_hash":"5e37f30824f460d6e6a480cef5ac1930ccc282b30e71a812fb1ac77c4bc18998","event_type":"lease.acquire","payload":{"lease_token":2,"prev_token":1,"ttl_s":600},"prev_hash":"6ffb3956bf9b16c93b8169bcee282f66ec0e18bbf68bdb74eb0d9380f395ac9f","timestamp":"2026-02-19T14:47:12.776633+00:00"}`
- `{"actor":"--interval","event_hash":"bc6808db7e094251cf84f20e3e215214a4647bf65c65ef4470e8e2418f98cf7c","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":2,"msgs":0},"prev_hash":"5e37f30824f460d6e6a480cef5ac1930ccc282b30e71a812fb1ac77c4bc18998","timestamp":"2026-02-19T14:47:12.777912+00:00"}`
- `{"actor":"--interval","event_hash":"04cc2e61b311f127482d897f5cf5ed83c0cf84f152021a2d574b936d55d852d1","event_type":"lease.acquire","payload":{"lease_token":3,"prev_token":2,"ttl_s":600},"prev_hash":"bc6808db7e094251cf84f20e3e215214a4647bf65c65ef4470e8e2418f98cf7c","timestamp":"2026-02-19T14:51:44.691208+00:00"}`
- `{"actor":"--interval","event_hash":"83e32c59b0338bada730fc4c56eafaf7bc60768d8f852e0ebce855fc0f90d0f1","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":3,"msgs":0},"prev_hash":"04cc2e61b311f127482d897f5cf5ed83c0cf84f152021a2d574b936d55d852d1","timestamp":"2026-02-19T14:51:44.692800+00:00"}`
- `{"actor":"--interval","event_hash":"2c089559e69f013200055dcb77c91d0712e7723109b7251ac3af477a530dc39b","event_type":"lease.acquire","payload":{"lease_token":4,"prev_token":3,"ttl_s":600},"prev_hash":"83e32c59b0338bada730fc4c56eafaf7bc60768d8f852e0ebce855fc0f90d0f1","timestamp":"2026-02-19T14:52:43.481246+00:00"}`
- `{"actor":"--interval","event_hash":"8b23280cce6d84ae122404d399e5f4d8d115fc1ba974853b256171988382f8ce","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":4,"msgs":0},"prev_hash":"2c089559e69f013200055dcb77c91d0712e7723109b7251ac3af477a530dc39b","timestamp":"2026-02-19T14:52:43.482569+00:00"}`
- `{"actor":"--interval","event_hash":"b6ad5dc2e1815eab7e8a9f365c9492b90c9a823cab16d9d98368630571c6676f","event_type":"lease.acquire","payload":{"lease_token":5,"prev_token":4,"ttl_s":600},"prev_hash":"8b23280cce6d84ae122404d399e5f4d8d115fc1ba974853b256171988382f8ce","timestamp":"2026-02-19T14:58:03.906281+00:00"}`
- `{"actor":"--interval","event_hash":"408d6d939af6ac2be9b44597321c883d820d0814e050deaf5b6d32c0790f4de0","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":5,"msgs":0},"prev_hash":"b6ad5dc2e1815eab7e8a9f365c9492b90c9a823cab16d9d98368630571c6676f","timestamp":"2026-02-19T14:58:03.908088+00:00"}`
- `{"actor":"--interval","event_hash":"792d680e99a9cedce4ec224ab8a6eecc8e92eec00f1aae156b838cbce2bbcdec","event_type":"lease.acquire","payload":{"lease_token":6,"prev_token":5,"ttl_s":600},"prev_hash":"408d6d939af6ac2be9b44597321c883d820d0814e050deaf5b6d32c0790f4de0","timestamp":"2026-02-19T15:00:25.758590+00:00"}`
- `{"actor":"--interval","event_hash":"6cc67b533aed8e8e2aa323d360aadb20e76e434f963a28971f04f2744b9d6465","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":6,"msgs":0},"prev_hash":"792d680e99a9cedce4ec224ab8a6eecc8e92eec00f1aae156b838cbce2bbcdec","timestamp":"2026-02-19T15:00:25.759891+00:00"}`
- `{"actor":"--interval","event_hash":"df1eef5c06ce4ae5f5e1d8a3e4dd6ec0e498f18a44e79a039efb727823c018e0","event_type":"lease.acquire","payload":{"lease_token":7,"prev_token":6,"ttl_s":600},"prev_hash":"6cc67b533aed8e8e2aa323d360aadb20e76e434f963a28971f04f2744b9d6465","timestamp":"2026-02-19T15:02:17.534832+00:00"}`
- `{"actor":"--interval","event_hash":"b382848a84fac752e0c20791afeffb6e98ab1690a7cb23cdf228df526fde53f6","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":7,"msgs":0},"prev_hash":"df1eef5c06ce4ae5f5e1d8a3e4dd6ec0e498f18a44e79a039efb727823c018e0","timestamp":"2026-02-19T15:02:17.535871+00:00"}`
- `{"actor":"--interval","event_hash":"5cd49ef272962785d692d1fb32d564acec75a00e0d51febe6e9a836bb7a52fef","event_type":"lease.acquire","payload":{"lease_token":8,"prev_token":7,"ttl_s":600},"prev_hash":"b382848a84fac752e0c20791afeffb6e98ab1690a7cb23cdf228df526fde53f6","timestamp":"2026-02-19T15:02:36.554231+00:00"}`
- `{"actor":"--interval","event_hash":"feeacff5eb27a23f9fa04d16c76e8868eb747aed4f3be4b050a232058b5fac46","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":8,"msgs":0},"prev_hash":"5cd49ef272962785d692d1fb32d564acec75a00e0d51febe6e9a836bb7a52fef","timestamp":"2026-02-19T15:02:36.555301+00:00"}`
- `{"actor":"gpt","event_hash":"4cd7086ebf10f16649fe672f33245149c83d54effe0bd4bc559ee2a9658ce010","event_type":"gpt.ping","payload":{"msg":"alive","ts":"2026-02-19T15:03:24.901300Z"},"prev_hash":"feeacff5eb27a23f9fa04d16c76e8868eb747aed4f3be4b050a232058b5fac46","timestamp":"2026-02-19T15:03:24.902343+00:00"}`
- `{"actor":"gpt","event_hash":"5a5df6f317a0bcc440a4f8f9fd5f09eee210b2aca126f416d7211e6f3905f7ec","event_type":"lease.acquire","payload":{"lease_token":1,"prev_token":0,"ttl_s":600},"prev_hash":"4cd7086ebf10f16649fe672f33245149c83d54effe0bd4bc559ee2a9658ce010","timestamp":"2026-02-19T15:04:16.841008+00:00"}`
- `{"actor":"gpt","event_hash":"14115638ff4556f9026bf555685b215c283d2b07a03c82ae461e74f57f9ab573","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":1,"msgs":0},"prev_hash":"5a5df6f317a0bcc440a4f8f9fd5f09eee210b2aca126f416d7211e6f3905f7ec","timestamp":"2026-02-19T15:04:16.842056+00:00"}`
- `{"actor":"ORION","event_hash":"d5b5ec61e55f1f7e4a14484699d2ad0a08eb33449dd5fc507c5e2d942c80749b","event_type":"relay.enqueue","payload":{"msg_id":"19c76eed821-3305ba14cf504884a61d","seq":50,"target":"GPT"},"prev_hash":"14115638ff4556f9026bf555685b215c283d2b07a03c82ae461e74f57f9ab573","timestamp":"2026-02-19T17:24:53.014651+00:00"}`
- `{"actor":"ORION","event_hash":"10873aac35282a16775b2acc6d1812af79d5a71465e9526a8eabf98094378396","event_type":"relay.enqueue","payload":{"msg_id":"19c7706b2f3-e8a9bd73406b4b708a42","seq":51,"target":"LEAD"},"prev_hash":"d5b5ec61e55f1f7e4a14484699d2ad0a08eb33449dd5fc507c5e2d942c80749b","timestamp":"2026-02-19T17:50:55.558001+00:00"}`
- `{"actor":"LEAD","event_hash":"9dcb6d62070bfffa231d69dc5c8373cc3ea3600555378ec97ae718094a24857e","event_type":"lease.acquire","payload":{"lease_token":4,"prev_token":3,"ttl_s":600},"prev_hash":"10873aac35282a16775b2acc6d1812af79d5a71465e9526a8eabf98094378396","timestamp":"2026-02-19T17:51:07.234491+00:00"}`
- `{"actor":"LEAD","event_hash":"8600bc2b2c4a9e5308f66b157f6601f73e6b504e65e56b099608f57f284ad460","event_type":"boot.complete","payload":{"last_seq":51,"lease_token":4,"msgs":1},"prev_hash":"9dcb6d62070bfffa231d69dc5c8373cc3ea3600555378ec97ae718094a24857e","timestamp":"2026-02-19T17:51:10.093774+00:00"}`
- `{"actor":"B2","event_hash":"344bc9e4deee498d97e582a09dd2b7e3c51c96e239b026cdb850f99bd4d5a521","event_type":"lease.acquire","payload":{"lease_token":1,"prev_token":0,"ttl_s":600},"prev_hash":"8600bc2b2c4a9e5308f66b157f6601f73e6b504e65e56b099608f57f284ad460","timestamp":"2026-02-19T17:51:11.542863+00:00"}`
- `{"actor":"B2","event_hash":"4d3a7e33445e99ebd37339d52cf70f4c03f3a87b95394e6bd7abc8913bc75e07","event_type":"boot.complete","payload":{"last_seq":50,"lease_token":1,"msgs":1},"prev_hash":"344bc9e4deee498d97e582a09dd2b7e3c51c96e239b026cdb850f99bd4d5a521","timestamp":"2026-02-19T17:51:15.632130+00:00"}`
- `{"actor":"gpt","event_hash":"508da68b14508afa680a505f179c5fcd19dca725efdd19f0fbb87c5957f15082","event_type":"lease.acquire","payload":{"lease_token":2,"prev_token":1,"ttl_s":600},"prev_hash":"4d3a7e33445e99ebd37339d52cf70f4c03f3a87b95394e6bd7abc8913bc75e07","timestamp":"2026-02-19T18:27:44.076886+00:00"}`
- `{"actor":"gpt","event_hash":"daf5014956baefd1b91687565e739578a7fdaa1bcdaa0e47d3d6a226aab41601","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":2,"msgs":0},"prev_hash":"508da68b14508afa680a505f179c5fcd19dca725efdd19f0fbb87c5957f15082","timestamp":"2026-02-19T18:27:44.078725+00:00"}`
- `{"actor":"gpt","event_hash":"d7f3353be9bc98077dddf984eded5da975fa1dc31b54d22f60988915b819ab9d","event_type":"lease.acquire","payload":{"lease_token":3,"prev_token":2,"ttl_s":600},"prev_hash":"daf5014956baefd1b91687565e739578a7fdaa1bcdaa0e47d3d6a226aab41601","timestamp":"2026-02-19T18:29:02.854618+00:00"}`
- `{"actor":"gpt","event_hash":"213812d416acab9bd1aa7ed1159318922f63787c93161a3ef5301213c04e8a1c","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":3,"msgs":0},"prev_hash":"d7f3353be9bc98077dddf984eded5da975fa1dc31b54d22f60988915b819ab9d","timestamp":"2026-02-19T18:29:02.856300+00:00"}`
- `{"actor":"gpt","event_hash":"c5539db33e913342b84413279afad515554fa980e2594325266b8470f2d96faf","event_type":"lease.acquire","payload":{"lease_token":4,"prev_token":3,"ttl_s":600},"prev_hash":"213812d416acab9bd1aa7ed1159318922f63787c93161a3ef5301213c04e8a1c","timestamp":"2026-02-19T18:29:26.073596+00:00"}`
- `{"actor":"gpt","event_hash":"0a415433f34024a10ae84454eee97741251610abb5aefffcfad506255f68a2e1","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":4,"msgs":0},"prev_hash":"c5539db33e913342b84413279afad515554fa980e2594325266b8470f2d96faf","timestamp":"2026-02-19T18:29:26.074955+00:00"}`
- `{"actor":"gpt","event_hash":"a343b0ac6d163aea36babcf50f04e2e03ae6bf5fca1ec052fcda5e3e3d66d366","event_type":"lease.acquire","payload":{"lease_token":5,"prev_token":4,"ttl_s":600},"prev_hash":"0a415433f34024a10ae84454eee97741251610abb5aefffcfad506255f68a2e1","timestamp":"2026-02-19T18:30:48.410157+00:00"}`
- `{"actor":"gpt","event_hash":"56f08e44d5f6c0c22eb8dcfe80a30538342565c2bdfd8310c80efa78b8ce3340","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":5,"msgs":0},"prev_hash":"a343b0ac6d163aea36babcf50f04e2e03ae6bf5fca1ec052fcda5e3e3d66d366","timestamp":"2026-02-19T18:30:48.411526+00:00"}`
- `{"actor":"gpt","event_hash":"7786ad2a4b483b5fbad84f48734c32ee8dd7d83962b205d9928d37a09c2f6022","event_type":"lease.acquire","payload":{"lease_token":6,"prev_token":5,"ttl_s":600},"prev_hash":"56f08e44d5f6c0c22eb8dcfe80a30538342565c2bdfd8310c80efa78b8ce3340","timestamp":"2026-02-19T18:36:01.471508+00:00"}`
- `{"actor":"gpt","event_hash":"75d43256b38a5bfdba53166f3a620516e2e2b7cf3b2ce64de5a46b8c45d7c1db","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":6,"msgs":0},"prev_hash":"7786ad2a4b483b5fbad84f48734c32ee8dd7d83962b205d9928d37a09c2f6022","timestamp":"2026-02-19T18:36:01.472879+00:00"}`
- `{"actor":"gpt","event_hash":"f7989eb6eb529dff7fa46de21bf741158211c50489982c37b5727654aa0950ea","event_type":"lease.acquire","payload":{"lease_token":7,"prev_token":6,"ttl_s":600},"prev_hash":"75d43256b38a5bfdba53166f3a620516e2e2b7cf3b2ce64de5a46b8c45d7c1db","timestamp":"2026-02-19T19:11:22.969759+00:00"}`
- `{"actor":"gpt","event_hash":"e4894c89fee6eb6c091fdf36727991b9d1359453247d75078b0043f6de29abad","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":7,"msgs":0},"prev_hash":"f7989eb6eb529dff7fa46de21bf741158211c50489982c37b5727654aa0950ea","timestamp":"2026-02-19T19:11:22.971221+00:00"}`
- `{"actor":"gpt","event_hash":"effac1f62007a7b11b4c50c526a71bcd1ace51f2baad7900e9625a387cb8c56e","event_type":"lease.acquire","payload":{"lease_token":8,"prev_token":7,"ttl_s":600},"prev_hash":"e4894c89fee6eb6c091fdf36727991b9d1359453247d75078b0043f6de29abad","timestamp":"2026-02-19T19:16:13.863201+00:00"}`
- `{"actor":"gpt","event_hash":"0b4186cd82d9e5704501b3f321f72be2fec4b6b837dfca6bd339854297211d0c","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":8,"msgs":0},"prev_hash":"effac1f62007a7b11b4c50c526a71bcd1ace51f2baad7900e9625a387cb8c56e","timestamp":"2026-02-19T19:16:13.864872+00:00"}`
- `{"actor":"COWORK","event_hash":"e9e5319ad40e1a077bdef8dae8c7000908cc5794b5133452091c8de4537f9b13","event_type":"relay.enqueue","payload":{"msg_id":"19c776bf10b-f34ec67783b44c16b0d0","seq":52,"target":"TEAMLEAD"},"prev_hash":"0b4186cd82d9e5704501b3f321f72be2fec4b6b837dfca6bd339854297211d0c","timestamp":"2026-02-19T19:41:28.718918+00:00"}`
- `{"actor":"COWORK","event_hash":"3131bf6bca1c26923e314323e4fd2e0ce6f1f82e70e4c5c2a57f17adfd1fbc77","event_type":"relay.enqueue","payload":{"msg_id":"19c776bf194-da78754113724f5d848f","seq":53,"target":"HYPERION"},"prev_hash":"e9e5319ad40e1a077bdef8dae8c7000908cc5794b5133452091c8de4537f9b13","timestamp":"2026-02-19T19:41:28.854164+00:00"}`
- `{"actor":"COWORK","event_hash":"315d7f183d06eb19473f21aa2168e670825f48ce87415899bf9b480adf9305c8","event_type":"relay.enqueue","payload":{"msg_id":"19c776bf21f-9296d9c2cc464c189a25","seq":54,"target":"ORION"},"prev_hash":"3131bf6bca1c26923e314323e4fd2e0ce6f1f82e70e4c5c2a57f17adfd1fbc77","timestamp":"2026-02-19T19:41:28.993250+00:00"}`
- `{"actor":"COWORK","event_hash":"2190020c3b722ea1dbd7ff0caf607c66372c6717c9d95deecab5c6de8a71dfde","event_type":"relay.enqueue","payload":{"msg_id":"19c776bf2a7-dd6b1b93bdd1457aacd3","seq":55,"target":"gpt"},"prev_hash":"315d7f183d06eb19473f21aa2168e670825f48ce87415899bf9b480adf9305c8","timestamp":"2026-02-19T19:41:29.128850+00:00"}`
- `{"actor":"gpt","event_hash":"4d8707031e8a4525001f1056d0c3dad4a1cac4086ede0d23e28410b2033dd14b","event_type":"lease.acquire","payload":{"lease_token":9,"prev_token":8,"ttl_s":600},"prev_hash":"2190020c3b722ea1dbd7ff0caf607c66372c6717c9d95deecab5c6de8a71dfde","timestamp":"2026-02-19T19:46:10.435252+00:00"}`
- `{"actor":"gpt","event_hash":"783cad17a3e6b656e47fe96edc7618010a3664b219b98c027ec219f4aa933634","event_type":"boot.complete","payload":{"last_seq":55,"lease_token":9,"msgs":1},"prev_hash":"4d8707031e8a4525001f1056d0c3dad4a1cac4086ede0d23e28410b2033dd14b","timestamp":"2026-02-19T19:46:10.437077+00:00"}`
- `{"actor":"gpt","event_hash":"356f98a06849292ac8caaf5763830721db463bd45a72795d9af5d609ab03c1f3","event_type":"lease.acquire","payload":{"lease_token":10,"prev_token":9,"ttl_s":600},"prev_hash":"783cad17a3e6b656e47fe96edc7618010a3664b219b98c027ec219f4aa933634","timestamp":"2026-02-19T19:48:31.430217+00:00"}`
- `{"actor":"gpt","event_hash":"6a3731a48d5838ae7b55f8bab8ba8fb837d1ea7dfbe482b1629559779f122d37","event_type":"boot.complete","payload":{"last_seq":55,"lease_token":10,"msgs":0},"prev_hash":"356f98a06849292ac8caaf5763830721db463bd45a72795d9af5d609ab03c1f3","timestamp":"2026-02-19T19:48:31.431773+00:00"}`
- `{"actor":"gpt","event_hash":"590c1b8d2b50515d149e64c1df10858b4f9aa2e6a6623362a13a76789af34afa","event_type":"lease.acquire","payload":{"lease_token":11,"prev_token":10,"ttl_s":600},"prev_hash":"6a3731a48d5838ae7b55f8bab8ba8fb837d1ea7dfbe482b1629559779f122d37","timestamp":"2026-02-19T20:58:08.822618+00:00"}`
- `{"actor":"gpt","event_hash":"26a368bdef7637149c0a2399bc6a0a38996658011899f75a563eec6d42d012ef","event_type":"boot.complete","payload":{"last_seq":55,"lease_token":11,"msgs":0},"prev_hash":"590c1b8d2b50515d149e64c1df10858b4f9aa2e6a6623362a13a76789af34afa","timestamp":"2026-02-19T20:58:08.824211+00:00"}`
- `{"actor":"GPT","event_hash":"80e6dffe3955ebf34966c7e1b742f994dad2ed6c577969884f8287c85f01c2c7","event_type":"relay.enqueue","payload":{"msg_id":"19c77b6721c-db769fa2e20b4b548a68","seq":56,"target":"LEAD"},"prev_hash":"26a368bdef7637149c0a2399bc6a0a38996658011899f75a563eec6d42d012ef","timestamp":"2026-02-19T21:02:51.423163+00:00"}`
- `{"actor":"GPT","event_hash":"bacd87b3e8e7ba5d6b27ee28573ca9a27c9b9c8b1f97ef3e5176a1a445620e68","event_type":"relay.enqueue","payload":{"msg_id":"19c77b672c9-1d826c12cf0a4b61a28f","seq":57,"target":"COWORK"},"prev_hash":"80e6dffe3955ebf34966c7e1b742f994dad2ed6c577969884f8287c85f01c2c7","timestamp":"2026-02-19T21:02:51.594927+00:00"}`
- `{"actor":"GPT","event_hash":"98d20611ca1af6f824bbe813c5b18887a2f8296baf6d177a8a0e90b31577886d","event_type":"relay.enqueue","payload":{"msg_id":"19c77b67356-49280517f1aa4eadb400","seq":58,"target":"ORION"},"prev_hash":"bacd87b3e8e7ba5d6b27ee28573ca9a27c9b9c8b1f97ef3e5176a1a445620e68","timestamp":"2026-02-19T21:02:51.735634+00:00"}`
- `{"actor":"GPT","event_hash":"3a4502c2c895134e0ee55bede09861657978c1a26ed1282d66199fc3abb9459b","event_type":"relay.enqueue","payload":{"msg_id":"19c77b673e2-57a45e727a4b41dea397","seq":59,"target":"HYPERION"},"prev_hash":"98d20611ca1af6f824bbe813c5b18887a2f8296baf6d177a8a0e90b31577886d","timestamp":"2026-02-19T21:02:51.876402+00:00"}`
- `{"actor":"GPT","event_hash":"35dd3c9bdb32f4bcdcc5326f84b521a6cc553872a3b8db7ef77e41c55ca8a439","event_type":"relay.enqueue","payload":{"msg_id":"19c77b7a9aa-4eb62fcbf75d44b78047","seq":60,"target":"LEAD"},"prev_hash":"3a4502c2c895134e0ee55bede09861657978c1a26ed1282d66199fc3abb9459b","timestamp":"2026-02-19T21:04:11.180414+00:00"}`
- `{"actor":"GPT","event_hash":"55ac9717b0ad3a942e07d3101790281d940b2b3a22daa35da811503d957da9ba","event_type":"relay.enqueue","payload":{"msg_id":"19c77bccf59-3e49a50000f84fee983a","seq":61,"target":"LEAD"},"prev_hash":"35dd3c9bdb32f4bcdcc5326f84b521a6cc553872a3b8db7ef77e41c55ca8a439","timestamp":"2026-02-19T21:09:48.507613+00:00"}`
- `{"actor":"GPT","event_hash":"7aa3cb0c5e5e63c7a09a0f96a37e6f69529f471e94118d067a4738c93a762758","event_type":"relay.enqueue","payload":{"msg_id":"19c77bccfde-34c7864bee3346a88b41","seq":62,"target":"COWORK"},"prev_hash":"55ac9717b0ad3a942e07d3101790281d940b2b3a22daa35da811503d957da9ba","timestamp":"2026-02-19T21:09:48.640067+00:00"}`
- `{"actor":"GPT","event_hash":"5ab9fde25e66df6695983db7e74554716c3d00fad0547ec7955b20fa30185680","event_type":"relay.enqueue","payload":{"msg_id":"19c77bcd064-f3aa725003c140a8ac0c","seq":63,"target":"ORION"},"prev_hash":"7aa3cb0c5e5e63c7a09a0f96a37e6f69529f471e94118d067a4738c93a762758","timestamp":"2026-02-19T21:09:48.773382+00:00"}`
- `{"actor":"GPT","event_hash":"97788d99a0c4e33855fe5f0f45ee7fc54f8d16710491ef527ff8153208967f94","event_type":"relay.enqueue","payload":{"msg_id":"19c77bcd0e7-6e70f036e1d9458ebb8e","seq":64,"target":"HYPERION"},"prev_hash":"5ab9fde25e66df6695983db7e74554716c3d00fad0547ec7955b20fa30185680","timestamp":"2026-02-19T21:09:48.905285+00:00"}`
- `{"actor":"GPT","event_hash":"72de7012dfd5269bb1c709489d23c34a9be2c4a36a3ffe83fbdcbde3e5f92cdf","event_type":"relay.enqueue","payload":{"msg_id":"19c77bcd16b-205d9389ab3c42c3943b","seq":65,"target":"B2"},"prev_hash":"97788d99a0c4e33855fe5f0f45ee7fc54f8d16710491ef527ff8153208967f94","timestamp":"2026-02-19T21:09:49.036528+00:00"}`
- `{"actor":"GPT","event_hash":"6dfa1e1f5c5b2effe1e52a220d2a20a8fef2c3bfbe114574bff55f0b431655c4","event_type":"relay.enqueue","payload":{"msg_id":"19c77bcd1ef-ce89945d23204d069603","seq":66,"target":"TEAMLEAD"},"prev_hash":"72de7012dfd5269bb1c709489d23c34a9be2c4a36a3ffe83fbdcbde3e5f92cdf","timestamp":"2026-02-19T21:09:49.168546+00:00"}`
- `{"actor":"GPT","event_hash":"6249d86de9f43be6f633902408180d602d0c7c44937ebe27a727bc44578d38bd","event_type":"relay.enqueue","payload":{"msg_id":"19c77bff62e-b8ecc96c634a4b0f8210","seq":67,"target":"B2"},"prev_hash":"6dfa1e1f5c5b2effe1e52a220d2a20a8fef2c3bfbe114574bff55f0b431655c4","timestamp":"2026-02-19T21:13:15.057148+00:00"}`
- `{"actor":"GPT","event_hash":"c959a678e322a7d643880fa18e54dd713f28d7a1f7be0de14bb74d7cddf7032e","event_type":"relay.enqueue","payload":{"msg_id":"19c77c03246-6d2332c4effb490e80fb","seq":68,"target":"LEAD"},"prev_hash":"6249d86de9f43be6f633902408180d602d0c7c44937ebe27a727bc44578d38bd","timestamp":"2026-02-19T21:13:30.440634+00:00"}`
- `{"actor":"GPT","event_hash":"91490302eae9356adb7734f797053dcc93ca5174749d2d3246ce880aa676dec5","event_type":"relay.enqueue","payload":{"msg_id":"19c77c0509d-9eafd027e98d4db98ad2","seq":69,"target":"B2"},"prev_hash":"c959a678e322a7d643880fa18e54dd713f28d7a1f7be0de14bb74d7cddf7032e","timestamp":"2026-02-19T21:13:38.206617+00:00"}`
- `{"actor":"GPT","event_hash":"a94fafaba53d8b7c3baf879e74b9e517a85e64c41c422b05c22ce772722e3004","event_type":"relay.enqueue","payload":{"msg_id":"19c77c4de32-34f2946baf3b491d8dcf","seq":70,"target":"B2"},"prev_hash":"91490302eae9356adb7734f797053dcc93ca5174749d2d3246ce880aa676dec5","timestamp":"2026-02-19T21:18:36.597706+00:00"}`
- `{"actor":"GPT","event_hash":"ac1bf8a51ea590c0363f87c63369f4d4a26dd590e53b5d5d0d3786d2ef6de516","event_type":"relay.enqueue","payload":{"msg_id":"19c77cef59d-ee337cf2c2234deaa081","seq":71,"target":"ORION"},"prev_hash":"a94fafaba53d8b7c3baf879e74b9e517a85e64c41c422b05c22ce772722e3004","timestamp":"2026-02-19T21:29:37.952318+00:00"}`
- `{"actor":"GPT","event_hash":"d649bf3b763138e0e339eae075d38dbff7b1c469e49e35131fca530ee93cce56","event_type":"relay.enqueue","payload":{"msg_id":"19c77dc7c63-e701174e45b74b99917b","seq":72,"target":"ORION"},"prev_hash":"ac1bf8a51ea590c0363f87c63369f4d4a26dd590e53b5d5d0d3786d2ef6de516","timestamp":"2026-02-19T21:44:24.422048+00:00"}`
- `{"actor":"ORION","event_hash":"41c014cf52f8adcccd64f44f12e5e33d688829c9e5fe59cd51ebd3f8b82c3b38","event_type":"relay.enqueue","payload":{"msg_id":"19c77dd4368-84cf9046cb9245569a37","seq":73,"target":"GPT"},"prev_hash":"d649bf3b763138e0e339eae075d38dbff7b1c469e49e35131fca530ee93cce56","timestamp":"2026-02-19T21:45:17.409420+00:00"}`
- `{"actor":"ORION","event_hash":"dd14fb37c77bb0b05e25c75bc3a777d7df6c68077837894dae1863f62df7de2c","event_type":"relay.enqueue","payload":{"msg_id":"19c77eee6fe-f64bb1aa1db84d6f8ea0","seq":74,"target":"B2"},"prev_hash":"41c014cf52f8adcccd64f44f12e5e33d688829c9e5fe59cd51ebd3f8b82c3b38","timestamp":"2026-02-19T22:04:33.491784+00:00"}`
- `{"actor":"ORION","event_hash":"940a0dc7309df656fee6821db6273ae1e904a7ce17ef80ae146209439d7ec4ea","event_type":"relay.enqueue","payload":{"msg_id":"19c77eeeff7-f1c0bdfc20274c35b2c8","seq":75,"target":"LEAD"},"prev_hash":"dd14fb37c77bb0b05e25c75bc3a777d7df6c68077837894dae1863f62df7de2c","timestamp":"2026-02-19T22:04:34.927680+00:00"}`
- `{"actor":"ORION","event_hash":"48e08684cd75b7edbd5411d5753318cf1f03c480bf835eca0046176b74f352fe","event_type":"relay.enqueue","payload":{"msg_id":"19c77faf413-2d03aec625944a5cb1bb","seq":76,"target":"GPT"},"prev_hash":"940a0dc7309df656fee6821db6273ae1e904a7ce17ef80ae146209439d7ec4ea","timestamp":"2026-02-19T22:17:42.460872+00:00"}`
- `{"actor":"ORION","event_hash":"60a3d05e3108404db9aeb8d71cdb43b0e5a4c9b9fca7628abedf64fded2212fa","event_type":"relay.enqueue","payload":{"msg_id":"19c77fd7d9c-558df524cc484523a3f1","seq":77,"target":"LEAD"},"prev_hash":"48e08684cd75b7edbd5411d5753318cf1f03c480bf835eca0046176b74f352fe","timestamp":"2026-02-19T22:20:28.585353+00:00"}`
- `{"actor":"REX","event_hash":"af6c83bcce89fc5428c57478e4b2a1f34bca33745794cfab25503513e6869260","event_type":"relay.enqueue","payload":{"msg_id":"19c7800abaa-0cf17870a762467c9bab","seq":78,"target":"GPT"},"prev_hash":"60a3d05e3108404db9aeb8d71cdb43b0e5a4c9b9fca7628abedf64fded2212fa","timestamp":"2026-02-19T22:23:55.819649+00:00"}`
- `{"actor":"GPT","event_hash":"e41612bfae8c45f9e5204391d6aac4d0b9d8a87bf774b84b366bf4d508de70e6","event_type":"relay.enqueue","payload":{"msg_id":"19c7800c588-ea9a7467c5d14d26b543","seq":79,"target":"REX"},"prev_hash":"af6c83bcce89fc5428c57478e4b2a1f34bca33745794cfab25503513e6869260","timestamp":"2026-02-19T22:24:02.442070+00:00"}`
- `{"actor":"REX","event_hash":"8ecd163e10db8b29ed787f4d411b0e033dbf51447bb52ed0397e856a680aa806","event_type":"lease.acquire","payload":{"lease_token":1,"prev_token":0,"ttl_s":600},"prev_hash":"e41612bfae8c45f9e5204391d6aac4d0b9d8a87bf774b84b366bf4d508de70e6","timestamp":"2026-02-19T22:24:29.700307+00:00"}`
- `{"actor":"REX","event_hash":"5ef9d7ab547ae6b58b03f16b80c14959c03cad9a9e94b07c1294d4c3d96071b7","event_type":"boot.complete","payload":{"last_seq":0,"lease_token":1,"msgs":0},"prev_hash":"8ecd163e10db8b29ed787f4d411b0e033dbf51447bb52ed0397e856a680aa806","timestamp":"2026-02-19T22:24:29.701736+00:00"}`
- `{"actor":"GPT","event_hash":"03940c71df1d6b14b934e49754e90a4cb0ef2e945c4d159987751f4cdcf1d358","event_type":"relay.enqueue","payload":{"msg_id":"19c78014ece-e14e43afdf4947eca137","seq":80,"target":"REX"},"prev_hash":"5ef9d7ab547ae6b58b03f16b80c14959c03cad9a9e94b07c1294d4c3d96071b7","timestamp":"2026-02-19T22:24:37.584064+00:00"}`
- `{"actor":"GPT","event_hash":"c5187671f4091abb6ee8a2ef362ae4d08b5523aaab0130ece1e2c746dee8d563","event_type":"relay.enqueue","payload":{"msg_id":"19c7802a45e-42caca070d59448f8075","seq":81,"target":"LEAD"},"prev_hash":"03940c71df1d6b14b934e49754e90a4cb0ef2e945c4d159987751f4cdcf1d358","timestamp":"2026-02-19T22:26:05.023803+00:00"}`

## 5) CHECKLIST
- Verify stop sentinel path exists and is monitored.
- Verify lease expirations and snapshot timestamps are fresh.
- Verify relay chain tail parses as JSON and remains append-only.
- Re-run exporter; confirm STATE_HASH only changes when payload changes.
