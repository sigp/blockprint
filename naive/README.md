## Naive Estimate

> This method has been superseded by the k-NN classifier. See the top-level README.

To run an estimate using the method from the original tweet:

```bash
curl "http://localhost:5052/lighthouse/block_rewards?start_slot=2151489&end_slot=2151694" > data.json
./client_diversity.py data.json
```

```
Lighthouse,0.22
Prysm,0.65
Teku,0.055
Teku or Nimbus,0.075
```

Adjust the start and end slots to a wider range for better accuracy, or to see historical
trends.
