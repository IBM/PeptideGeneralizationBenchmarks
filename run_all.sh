rep=${1}
model=${2}

echo "|--------------------------------------------|"
echo "| Welcome to PeptideGeneralizationBenchmarks |"
echo "|           Powered by AutoPeptideML         |"
echo "|--------------------------------------------|"
echo "Running experiments for Representation: ${rep} and Model: ${model}\n"
echo "** Calculating representations **"

for dataset in c-binding c-cpp c-antibacterial c-antiviral nc-binding nc-cpp nc-antibacterial nc-antiviral; do
    echo "Dataset: ${dataset}"
    python rep_transfer/represent_peptides.py $dataset $rep --device mps
done

echo "** Interpolation experiments **"
for dataset in c-binding c-cpp c-antibacterial c-antiviral nc-binding nc-cpp nc-antibacterial nc-antiviral; do
    echo "Dataset: ${dataset}"
    python rep_transfer/evaluation.py $dataset $model $rep
done

echo "** Extrapolation experiments **"
for dataset in binding cpp antibacterial antiviral; do
    echo "Dataset: ${dataset}"
    python rep_transfer/evaluation_ood.py $dataset $model $rep
done