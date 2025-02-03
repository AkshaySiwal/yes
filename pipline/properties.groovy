properties([
    parameters([
        choice(
            name: 'SELECTION_TYPE',
            choices: ['', 'File', 'Manual'],
            description: 'Select input type'
        )
    ])
])

if (SELECTION_TYPE == 'Manual') {
    properties([
        parameters([
            choice(
                name: 'SELECTION_TYPE',
                choices: ['', 'File', 'Manual'],
                description: 'Select input type'
            ),
            string(
                name: 'ACCOUNT',
                defaultValue: '',
                description: 'Enter Account ID',
                trim: true
            ),
            string(
                name: 'ROLE',
                defaultValue: '',
                description: 'Enter Role Name',
                trim: true
            )
        ])
    ])
} else if (SELECTION_TYPE == 'File') {
    properties([
        parameters([
            choice(
                name: 'SELECTION_TYPE',
                choices: ['', 'File', 'Manual'],
                description: 'Select input type'
            ),
            file(
                name: 'INPUT_FILE',
                description: 'Upload your input file'
            )
        ])
    ])
}
