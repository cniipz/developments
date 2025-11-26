#!/bin/bash

/bin/lsblk -dn -o NAME,TYPE,TRAN \
	| awk '$2=="disk" && ($3 == "nvme"){print "/dev/"$1}' \
  | /usr/bin/jq -R -s '
      split("\n")
      | map(select(length>0))
      | {data: map({"{#NVME_DISK}": .})}
    '
