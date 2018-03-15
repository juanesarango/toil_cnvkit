
1. The following files were used. 1 tumor, 2 normals.

    ```bash
    # Original Files
    TUMOR_BAM=I-H-100770-N1-1-D1-1.bam
    NORMAL1_BAM=I-H-100771-N1-1-D1-1.bam
    NORMAL2_BAM=I-H-100772-N1-1-D1-1.bam
    ```

1. The tumor file has a known Copy Number Variation around the following region:

    | chromosome	| start	    | end	    | ploidy	|
    | ------------- | --------- | --------	| --------  |
    | 5	            | 49406141	| 106750846	| 1	        |
    | 5	            | 106750846	| 166738641	| 2	        |

    So a region of `106750.846 +/- 10000000` is used to create the smaller files:
    ```bash
    # Region
    CHROMOSOME=5
    POS_START=96750846
    POS_END=116750846
    REGION=$CHROMOSOME:$POS_START-$POS_END

    # Creation of subsamples
    samtools view -b $TUMOR_BAM $REGION > tumor_src.bam
    samtools view -b $NORMAL1_BAM $REGION > normal1_src.bam
    samtools view -b $NORMAL2_BAM $REGION > normal2_src.bam
    ```
1. Then a small reference was created:

    ```bash
    # Subsample reference genome fasta file
    GENOME=gr37.fasta
    samtools faidx $GENOME $REGION > reference.fasta

    # rename chromosome
    sed -i "s/>$REGION/>$CHROMOSOME/" reference.fasta

    # index reference
    samtools faidx reference.fasta
    bwa index reference.fasta
    ```

1. Realign the samples files with this new reference:
    ```bash
    bwa_mem.pl -o . -reference reference.fasta -s tumor tumor_src.bam
    bwa_mem.pl -o . -reference reference.fasta -s normal1 normal1_src.bam
    bwa_mem.pl -o . -reference reference.fasta -s normal2 normal2_src.bam
    ```

1. Create the access bed file with the new reference:

    ```bash
    cnvkit.py access reference.fasta -o reference.access.bed
    ```

1. Create a targets bed file from HEMEPACT-V3 with only the cromosome 5:

    ```bash
    BED_FILE=HEMEPACT-V3.bed
    grep "^$CHROMOSOME" $BED_FILE > targets.bed
    ```
