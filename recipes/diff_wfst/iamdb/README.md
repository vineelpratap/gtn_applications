## Preparing the dataset

Register [here](https://fki.tic.heia-fr.ch/login) and run the following script to download the dataset:
```
sh ../../../datasets/download/iamdb.sh <path_to_data> <email> <password>
```

## Dense Transitions

| ngram      | No blank | Forced blank | Optonal blank |
| ----------- | ----------- | ----------- | ----------- |
| 0      | [ltr_ngram0_noblank.json](ltr_ngram0_noblank.json)  | [ltr_ngram0_forceblank.json](ltr_ngram0_forceblank.json)   | [ltr_ngram0_optblank.json](ltr_ngram0_optblank.json)       |
| 1   | [ltr_ngram1_noblank.json](ltr_ngram1_noblank.json)       | [ltr_ngram1_forceblank.json](ltr_ngram1_forceblank.json) | [ltr_ngram1_optblank.json](ltr_ngram1_optblank.json)       |
| 2   | [ltr_ngram2_noblank.json](ltr_ngram2_noblank.json)        | [ltr_ngram2_forceblank.json](ltr_ngram2_forceblank.json) | [ltr_ngram2_optblank.json](ltr_ngram2_optblank.json)       |


## Pruned Transitions

For preparing the list of letters and 1K wordpieces, use the following the script 
```

```


For creating pruned transitions graph (with backoff), use the following the script 
```

```

| Pruning      | Letters | 1K Wordpieces | 
| ----------- | ----------- | ----------- | 
| None      | [ltr_ngram2_optblank_prunenone.json](ltr_ngram2_optblank_prunenone.json)  | [1kwp_ngram2_optblank_prunenone.json](1kwp_ngram2_optblank_prunenone.json)   | 
| 0   | [ltr_ngram2_optblank_prune0.json](ltr_ngram2_optblank_prune0.json)       | [1kwp_ngram2_optblank_prune0.json](1kwp_ngram2_optblank_prune0.json) | 
| 10   | [ltr_ngram2_optblank_prune10.json](ltr_ngram2_optblank_prune10.json)        | [1kwp_ngram2_optblank_prune10.json](1kwp_ngram2_optblank_prune10.json) | 

For preparing the pruned ngram transition graph, use `../../../scripts/build_transitions.py`. 


