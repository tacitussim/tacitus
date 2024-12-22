# Tacitus Prototype

This prototype is _very_ early in development and quite basic, but essentially it works as follows:

In the `main.py` you'll find a map called `nodes`
This map contains the infrastructure nodes you'll interact with
You add each node, with its IP (if it't not an IAM accessed resource) along with ingress/egress rules and setting `use_ingress` and `use_egress` to `True`, respectively
If you want to use IAM to access something (like an S3 bucket) set `use_access` to `True` and an access policy Example ingress and egress rules as well as access policies are shown in the example `nodes` variable

Finally, define your flows in the `flows` variable
Each entry is the next hop in the infrastructure, with `.pop` meaning "go back to the previous node"
If you're using an IAM resource format it as `<whatever you want>://<name of the resource node>:-1`

Finally, ensure you've installed the contents of `requirements.txt` (you'll need Python >- `3.10.0`) and run

```
python main.py
```

That will perform the simulation and startup the dashboard, you can then access [http://localhost:8080](http://localhost:8080) to view the dashboard