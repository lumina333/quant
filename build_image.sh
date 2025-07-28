#!/bin/bash

dir="$(realpath "$(dirname "$0")")"

cd "$dir"

docker build --network=host -t quant_app:v1 .


